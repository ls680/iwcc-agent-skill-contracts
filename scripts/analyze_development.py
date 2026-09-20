#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from iwcc.actions import parse_action
from iwcc.validator import validate_program


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def distance(left: list[str], right: list[str]) -> int:
    previous = list(range(len(right) + 1))
    for index, lvalue in enumerate(left, 1):
        current = [index]
        for jndex, rvalue in enumerate(right, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[jndex] + 1,
                    previous[jndex - 1] + int(lvalue != rvalue),
                )
            )
        previous = current
    return previous[-1]


def operator_sequence(program: list[str]) -> list[str]:
    return [parse_action(action).operator for action in program]


def metrics(labels: dict[str, bool], predictions: dict[str, bool]) -> dict:
    tp = sum(labels[key] and predictions[key] for key in labels)
    fn = sum(labels[key] and not predictions[key] for key in labels)
    tn = sum(not labels[key] and not predictions[key] for key in labels)
    fp = sum(not labels[key] and predictions[key] for key in labels)
    recall, specificity = tp / (tp + fn), tn / (tn + fp)
    return {
        "true_positive": tp,
        "false_negative": fn,
        "true_negative": tn,
        "false_positive": fp,
        "recall": recall,
        "specificity": specificity,
        "false_rejection_rate": 1 - specificity,
        "balanced_accuracy": (recall + specificity) / 2,
    }


def main() -> None:
    config_path = PROJECT / "configs/development_v2.json"
    config = json.loads(config_path.read_text())
    public_path = PROJECT / "data/development/public_candidates.jsonl"
    label_path = PROJECT / "data/development/private_labels.jsonl"
    contract_path = PROJECT / "results/development/v2/contract.json"
    public = rows(public_path)
    private = {row["candidate_id"]: row for row in rows(label_path)}
    labels = {key: value["killed"] for key, value in private.items()}
    contract = json.loads(contract_path.read_text())
    if {row["candidate_id"] for row in public} != set(labels):
        raise RuntimeError("public/private development candidates differ")

    predictions: dict[str, dict[str, bool]] = defaultdict(dict)
    details = []
    for candidate in public:
        for mode in ("endpoint_only", "ordered_milestones", "iwcc"):
            result = validate_program(
                contract,
                environment=candidate["environment"],
                family=candidate["family"],
                objective=candidate["objective"],
                program=candidate["program"],
                mode=mode,
                initial_observation=candidate["initial_observation"],
            )
            predictions[mode][candidate["candidate_id"]] = not result["valid"]
        details.append({"candidate_id": candidate["candidate_id"], "label": labels[candidate["candidate_id"]]})

    training_sequences: dict[tuple[str, str], list[tuple[str, list[str]]]] = defaultdict(list)
    for candidate in public:
        if not labels[candidate["candidate_id"]]:
            training_sequences[(candidate["environment"], candidate["family"])].append(
                (private[candidate["candidate_id"]]["task_id"], operator_sequence(candidate["program"]))
            )
    nearest_scores = {}
    for candidate in public:
        sequence = operator_sequence(candidate["program"])
        task_id = private[candidate["candidate_id"]]["task_id"]
        candidates = [
            sequence
            for source_task, sequence in training_sequences[(candidate["environment"], candidate["family"])]
            if source_task != task_id
        ]
        if not candidates:
            candidates = [
                sequence
                for _, sequence in training_sequences[(candidate["environment"], candidate["family"])]
            ]
        nearest_scores[candidate["candidate_id"]] = min(
            distance(sequence, reference) / max(len(sequence), len(reference), 1)
            for reference in candidates
        )
    thresholds = sorted(set(nearest_scores.values()) | {0.0, 1.0})
    calibrated = []
    for threshold in thresholds:
        proposed = {key: value > threshold for key, value in nearest_scores.items()}
        result = metrics(labels, proposed)
        if result["specificity"] >= 0.95:
            calibrated.append((result["balanced_accuracy"], -threshold, threshold, result, proposed))
    _, _, nearest_threshold, nearest_metrics, nearest_predictions = max(calibrated)
    predictions["nearest_successful_trace"] = nearest_predictions

    model_config_path = PROJECT / "configs/models.json"
    model_config = json.loads(model_config_path.read_text())
    response_paths = {}
    for model in model_config["models"]:
        label = model["label"]
        path = PROJECT / "results/development/llm_judges" / label / "responses.jsonl"
        response_paths[label] = path
        responses = {row["candidate_id"]: row for row in rows(path)}
        if set(responses) != set(labels):
            raise RuntimeError(f"incomplete model judge: {label}")
        predictions[f"llm_{label}"] = {
            key: row["verdict"] == "BROKEN" for key, row in responses.items()
        }

    all_metrics = {name: metrics(labels, values) for name, values in predictions.items()}
    comparators = [name for name in all_metrics if name != "iwcc"]
    strongest = max(comparators, key=lambda name: all_metrics[name]["balanced_accuracy"])
    gain = all_metrics["iwcc"]["balanced_accuracy"] - all_metrics[strongest]["balanced_accuracy"]
    by_environment = {}
    for environment in sorted({row["environment"] for row in public}):
        keys = {row["candidate_id"] for row in public if row["environment"] == environment}
        group_labels = {key: labels[key] for key in keys}
        by_environment[environment] = {
            name: metrics(group_labels, {key: values[key] for key in keys})
            for name, values in predictions.items()
        }
    gates = config["development_gates"]
    summary = {
        "status": "development_strong_controls_complete",
        "candidate_programs": len(labels),
        "killed": sum(labels.values()),
        "controls": sum(not value for value in labels.values()),
        "metrics": all_metrics,
        "nearest_successful_trace_threshold": nearest_threshold,
        "nearest_threshold_calibration": "maximum development balanced accuracy subject to specificity >= 0.95",
        "strongest_nonoracle_comparator": strongest,
        "absolute_gain": gain,
        "by_environment": by_environment,
        "gates": {
            "balanced_accuracy": all_metrics["iwcc"]["balanced_accuracy"] >= gates["minimum_balanced_accuracy"],
            "gain_at_least_10_points": gain >= gates["minimum_gain_points"] / 100,
            "false_rejection_at_most_5_percent": all_metrics["iwcc"]["false_rejection_rate"] <= gates["maximum_false_rejection_rate"],
            "recall_at_least_75_percent": all_metrics["iwcc"]["recall"] >= gates["minimum_killed_recall"],
            "positive_in_both_environments": all(
                values["iwcc"]["balanced_accuracy"] > values[strongest]["balanced_accuracy"]
                for values in by_environment.values()
            ),
        },
        "input_sha256": {
            "config": digest(config_path),
            "models": digest(model_config_path),
            "public_candidates": digest(public_path),
            "private_labels": digest(label_path),
            "contract": digest(contract_path),
            **{f"llm_{name}": digest(path) for name, path in response_paths.items()},
            "analyzer": digest(Path(__file__)),
        },
    }
    summary["all_development_gates_pass"] = all(summary["gates"].values())
    output = PROJECT / "results/development/final"
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (output / "predictions.jsonl").write_text(
        "".join(
            json.dumps(
                {
                    **row,
                    "nearest_score": nearest_scores[row["candidate_id"]],
                    **{name: values[row["candidate_id"]] for name, values in predictions.items()},
                },
                sort_keys=True,
            )
            + "\n"
            for row in details
        )
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
