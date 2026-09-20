#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import random
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
from native_common import digest, rows


def metrics(labels: list[bool], predictions: list[bool]) -> dict:
    tp = sum(label and prediction for label, prediction in zip(labels, predictions))
    fn = sum(label and not prediction for label, prediction in zip(labels, predictions))
    tn = sum(not label and not prediction for label, prediction in zip(labels, predictions))
    fp = sum(not label and prediction for label, prediction in zip(labels, predictions))
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    return {
        "true_positive": tp, "false_negative": fn, "true_negative": tn, "false_positive": fp,
        "recall": recall, "specificity": specificity,
        "false_rejection_rate": 1 - specificity,
        "balanced_accuracy": (recall + specificity) / 2,
    }


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower, upper = int(position), min(int(position) + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def subset_metrics(keys: list[str], labels: dict[str, bool], predictions: dict[str, bool]) -> dict:
    return metrics([labels[key] for key in keys], [predictions[key] for key in keys])


def task_bootstrap(private: dict[str, dict], labels: dict[str, bool], proposed: dict[str, bool], baseline: dict[str, bool], replicates: int, seed: str) -> list[float]:
    by_task: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for key, row in private.items():
        by_task[(row["environment"], row["family"], row["task_id"])].append(key)
    strata: dict[tuple[str, str], list[tuple[str, str, str]]] = defaultdict(list)
    for task in by_task:
        strata[task[:2]].append(task)
    rng, effects = random.Random(seed), []
    for _ in range(replicates):
        sampled = []
        for tasks in strata.values():
            for _ in tasks:
                sampled.extend(by_task[rng.choice(tasks)])
        effects.append(
            subset_metrics(sampled, labels, proposed)["balanced_accuracy"]
            - subset_metrics(sampled, labels, baseline)["balanced_accuracy"]
        )
    return effects


def task_effects(private: dict[str, dict], labels: dict[str, bool], proposed: dict[str, bool], baseline: dict[str, bool]) -> list[float]:
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for key, row in private.items():
        grouped[(row["environment"], row["task_id"])].append(key)
    return [
        subset_metrics(keys, labels, proposed)["balanced_accuracy"]
        - subset_metrics(keys, labels, baseline)["balanced_accuracy"]
        for keys in grouped.values()
    ]


def permutation_p(effects: list[float], replicates: int, seed: str) -> float:
    observed = sum(effects) / len(effects)
    rng, exceed = random.Random(seed), 0
    for _ in range(replicates):
        value = sum(effect if rng.random() < 0.5 else -effect for effect in effects) / len(effects)
        exceed += abs(value) >= abs(observed)
    return (exceed + 1) / (replicates + 1)


def main() -> None:
    config_path = PROJECT / "configs/confirmation.json"
    config = json.loads(config_path.read_text())
    lock_path = PROJECT / config["outputs"]["method_lock"]
    lock = json.loads(lock_path.read_text())
    for relative, expected in lock["file_sha256"].items():
        if digest(PROJECT / relative) != expected:
            raise RuntimeError(f"method-locked file changed: {relative}")
    candidate_dir = PROJECT / config["outputs"]["candidates"]
    public_path, private_path = candidate_dir / "public_candidates.jsonl", candidate_dir / "private_labels.jsonl"
    public = {row["candidate_id"]: row for row in rows(public_path)}
    private = {row["candidate_id"]: row for row in rows(private_path)}
    if set(public) != set(private):
        raise RuntimeError("public/private candidate sets differ")
    labels = {key: row["killed"] for key, row in private.items()}
    predictions_path = PROJECT / config["outputs"]["method_results"] / "predictions.jsonl"
    method_rows = {row["candidate_id"]: row for row in rows(predictions_path)}
    if set(method_rows) != set(labels):
        raise RuntimeError("incomplete deterministic predictions")
    predictions = {
        name: {key: row["predicted_broken"][name] for key, row in method_rows.items()}
        for name in ("endpoint_only", "ordered_milestones", "iwcc", "nearest_successful_trace")
    }
    models = json.loads((PROJECT / "configs/models.json").read_text())["models"]
    response_paths = {}
    for model in models:
        label = model["label"]
        path = PROJECT / config["outputs"]["llm_results"] / label / "responses.jsonl"
        response_paths[label] = path
        response = {row["candidate_id"]: row for row in rows(path)}
        if set(response) != set(labels):
            raise RuntimeError(f"incomplete model judge: {label}")
        predictions[f"llm_{label}"] = {key: row["verdict"] == "BROKEN" for key, row in response.items()}
    all_keys = list(labels)
    all_metrics = {name: subset_metrics(all_keys, labels, value) for name, value in predictions.items()}
    primary = config["primary_comparator"]
    gain = all_metrics["iwcc"]["balanced_accuracy"] - all_metrics[primary]["balanced_accuracy"]
    comparators = [name for name in predictions if name != "iwcc"]
    strongest = max(comparators, key=lambda name: all_metrics[name]["balanced_accuracy"])
    strongest_gain = all_metrics["iwcc"]["balanced_accuracy"] - all_metrics[strongest]["balanced_accuracy"]
    bootstrap = task_bootstrap(private, labels, predictions["iwcc"], predictions[primary], config["bootstrap_replicates"], config["analysis_seed"] + "::bootstrap")
    effects = task_effects(private, labels, predictions["iwcc"], predictions[primary])
    p_value = permutation_p(effects, config["permutation_replicates"], config["analysis_seed"] + "::permutation")
    by_environment, by_family = {}, {}
    for environment in sorted({row["environment"] for row in private.values()}):
        keys = [key for key, row in private.items() if row["environment"] == environment]
        by_environment[environment] = {name: subset_metrics(keys, labels, value) for name, value in predictions.items()}
    for environment, family in sorted({(row["environment"], row["family"]) for row in private.values()}):
        keys = [key for key, row in private.items() if row["environment"] == environment and row["family"] == family]
        by_family[f"{environment}/{family}"] = {name: subset_metrics(keys, labels, value) for name, value in predictions.items()}
    operator_recall = {}
    for operator in config["operators"]:
        keys = [key for key, row in private.items() if row.get("operator") == operator and labels[key]]
        operator_recall[operator] = {
            name: sum(value[key] for key in keys) / len(keys) if keys else None
            for name, value in predictions.items()
        }
    gates_config = config["gates"]
    gates = {
        "minimum_tasks": len({(row["environment"], row["task_id"]) for row in private.values()}) >= gates_config["minimum_tasks"],
        "minimum_killed": sum(labels.values()) >= gates_config["minimum_killed"],
        "minimum_controls": sum(not value for value in labels.values()) >= gates_config["minimum_controls"],
        "balanced_accuracy": all_metrics["iwcc"]["balanced_accuracy"] >= gates_config["minimum_balanced_accuracy"],
        "gain_at_least_10_points": gain >= gates_config["minimum_gain_points"] / 100,
        "false_rejection_at_most_5_percent": all_metrics["iwcc"]["false_rejection_rate"] <= gates_config["maximum_false_rejection_rate"],
        "recall_at_least_75_percent": all_metrics["iwcc"]["recall"] >= gates_config["minimum_killed_recall"],
        "bootstrap_lower_above_zero": percentile(bootstrap, 0.025) > 0,
        "paired_task_permutation_p_at_most_0_01": p_value <= config["alpha"],
        "positive_in_both_environments": all(
            group["iwcc"]["balanced_accuracy"] > group[primary]["balanced_accuracy"]
            for group in by_environment.values()
        ),
    }
    summary = {
        "status": "independent_confirmation_analyzed_once",
        "counts": {
            "candidate_programs": len(labels), "tasks": len({(row["environment"], row["task_id"]) for row in private.values()}),
            "killed": sum(labels.values()), "controls": sum(not value for value in labels.values()),
        },
        "metrics": all_metrics, "primary_comparator": primary,
        "absolute_gain": gain, "strongest_nonoracle_comparator": strongest,
        "gain_over_strongest_nonoracle": strongest_gain,
        "task_stratified_bootstrap_gain_95_ci": [percentile(bootstrap, 0.025), percentile(bootstrap, 0.975)],
        "paired_task_permutation_p": p_value,
        "by_environment": by_environment, "by_family": by_family,
        "killed_recall_by_operator": operator_recall,
        "confirmation_gates": gates, "confirmation_passed": all(gates.values()),
        "input_sha256": {
            "method_lock": digest(lock_path), "public_candidates": digest(public_path),
            "private_labels": digest(private_path), "program_predictions": digest(predictions_path),
            **{f"llm_{label}": digest(path) for label, path in response_paths.items()},
            "analyzer": digest(Path(__file__)),
        },
    }
    output = PROJECT / config["outputs"]["analysis"]
    output.mkdir(parents=True, exist_ok=True)
    summary_path = output / "summary.json"
    if summary_path.exists():
        raise RuntimeError("confirmation was already analyzed")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    detail_path = output / "predictions_with_private_labels.jsonl"
    detail_path.write_text("".join(json.dumps({
        "candidate_id": key, **private[key],
        **{name: value[key] for name, value in predictions.items()},
        "iwcc_violations": method_rows[key]["violations"]["iwcc"],
    }, sort_keys=True) + "\n" for key in all_keys))
    summary["details_sha256"] = digest(detail_path)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
