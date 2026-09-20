#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
import time

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from iwcc.compiler import ContractCompiler
from iwcc.validator import validate_program


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def mutate(actions: list[str], operator: str, index: int) -> list[str]:
    candidate = list(actions)
    if operator == "delete_action":
        del candidate[index]
    elif operator == "adjacent_order_swap":
        candidate[index], candidate[index + 1] = candidate[index + 1], candidate[index]
    elif operator == "truncate_suffix":
        candidate = candidate[:index]
    else:
        raise ValueError(operator)
    return candidate


def score(records: list[dict], mode: str) -> dict:
    tp = sum(row["killed"] and row[mode] for row in records)
    fn = sum(row["killed"] and not row[mode] for row in records)
    tn = sum(not row["killed"] and not row[mode] for row in records)
    fp = sum(not row["killed"] and row[mode] for row in records)
    recall = tp / (tp + fn)
    specificity = tn / (tn + fp)
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/development.json")
    arguments = parser.parse_args()
    config_path = PROJECT / arguments.config
    config = json.loads(config_path.read_text())
    paper4 = (PROJECT / config["paper4_root"]).resolve()
    paths = {name: paper4 / path for name, path in config["inputs"].items()}
    traces = [row for row in rows(paths["oracles"]) if row["success"] and not row["error"]]
    by_task = {(row["environment"], row["task_id"]): row for row in traces}
    outcomes = [row for row in rows(paths["mutation_outcomes"]) if not row["technical_error"]]

    started = time.perf_counter()
    compiler = ContractCompiler(
        config["minimum_clause_support"], config["minimum_order_support"]
    )
    for trace in traces:
        compiler.add(trace)
    successful_mutation_witnesses = []
    if config.get("include_successful_mutations_as_witnesses", False):
        for outcome in outcomes:
            if not outcome["success"]:
                continue
            parent = by_task[(outcome["environment"], outcome["task_id"])]
            witnessed = {
                **parent,
                "task_id": f"successful-mutation:{outcome['spec_id']}",
                "executed_actions": mutate(
                    parent["executed_actions"], outcome["operator"], outcome["program_index"]
                ),
            }
            compiler.add(witnessed)
            successful_mutation_witnesses.append(witnessed)
    contract = compiler.compile()

    permutation_hashes = []
    for seed in range(config["trace_order_permutations"]):
        shuffled = [*traces, *successful_mutation_witnesses]
        random.Random(seed).shuffle(shuffled)
        alternate = ContractCompiler(
            config["minimum_clause_support"], config["minimum_order_support"]
        )
        for trace in shuffled:
            alternate.add(trace)
        permutation_hashes.append(alternate.compile()["canonical_sha256"])

    records = []
    for trace in traces:
        base = {
            "candidate_id": f"healthy:{trace['environment']}:{trace['task_id']}",
            "environment": trace["environment"],
            "family": trace["family"],
            "task_id": trace["task_id"],
            "kind": "healthy",
            "operator": "identity",
            "program_index": None,
            "killed": False,
        }
        candidate = trace["executed_actions"]
        for mode in ("endpoint_only", "ordered_milestones", "iwcc"):
            result = validate_program(
                contract,
                environment=trace["environment"],
                family=trace["family"],
                objective=trace["task_description"],
                program=candidate,
                mode=mode,
                initial_observation=trace["observations"][0],
            )
            base[mode] = not result["valid"]
            base[f"{mode}_violations"] = result["violations"]
        records.append(base)
    for outcome in outcomes:
        trace = by_task[(outcome["environment"], outcome["task_id"])]
        candidate = mutate(
            trace["executed_actions"], outcome["operator"], outcome["program_index"]
        )
        base = {
            "candidate_id": outcome["spec_id"],
            "environment": outcome["environment"],
            "family": outcome["family"],
            "task_id": outcome["task_id"],
            "kind": "mutation",
            "operator": outcome["operator"],
            "program_index": outcome["program_index"],
            "killed": outcome["killed"],
        }
        for mode in ("endpoint_only", "ordered_milestones", "iwcc"):
            result = validate_program(
                contract,
                environment=trace["environment"],
                family=trace["family"],
                objective=trace["task_description"],
                program=candidate,
                mode=mode,
                initial_observation=trace["observations"][0],
            )
            base[mode] = not result["valid"]
            base[f"{mode}_violations"] = result["violations"]
        records.append(base)

    metrics = {
        mode: score(records, mode)
        for mode in ("endpoint_only", "ordered_milestones", "iwcc")
    }
    by_environment = {}
    for environment in sorted({row["environment"] for row in records}):
        group = [row for row in records if row["environment"] == environment]
        by_environment[environment] = {
            mode: score(group, mode)
            for mode in ("endpoint_only", "ordered_milestones", "iwcc")
        }
    strongest = max(
        ("endpoint_only", "ordered_milestones"),
        key=lambda mode: metrics[mode]["balanced_accuracy"],
    )
    gain = metrics["iwcc"]["balanced_accuracy"] - metrics[strongest]["balanced_accuracy"]
    gates = config["development_gates"]
    control_count = sum(not row["killed"] for row in records)
    killed_count = sum(row["killed"] for row in records)
    summary = {
        "status": config["status"] + "_complete",
        "healthy_traces": len(traces),
        "successful_mutation_witnesses": len(successful_mutation_witnesses),
        "mutation_outcomes": len(outcomes),
        "candidate_programs": len(records),
        "killed": killed_count,
        "controls": control_count,
        "by_kind": dict(Counter(row["kind"] for row in records)),
        "metrics": metrics,
        "strongest_nonmodel_comparator": strongest,
        "absolute_gain": gain,
        "by_environment": by_environment,
        "contract_sha256": contract["canonical_sha256"],
        "contract_order_invariant": len(set(permutation_hashes)) == 1,
        "all_clauses_witnessed": all(
            clause_ids
            for item in contract["contracts"].values()
            for clause_ids in item["witnesses"].values()
        ),
        "gates": {
            "enough_killed": killed_count >= gates["minimum_killed"],
            "enough_controls": control_count >= gates["minimum_controls"],
            "balanced_accuracy": metrics["iwcc"]["balanced_accuracy"] >= gates["minimum_balanced_accuracy"],
            "gain_at_least_10_points": gain >= gates["minimum_gain_points"] / 100,
            "false_rejection_at_most_5_percent": metrics["iwcc"]["false_rejection_rate"] <= gates["maximum_false_rejection_rate"],
            "recall_at_least_75_percent": metrics["iwcc"]["recall"] >= gates["minimum_killed_recall"],
            "positive_in_both_environments": all(
                values["iwcc"]["balanced_accuracy"]
                > values[strongest]["balanced_accuracy"]
                for values in by_environment.values()
            ),
            "order_invariant": len(set(permutation_hashes)) == 1,
        },
        "elapsed_seconds": time.perf_counter() - started,
        "input_sha256": {name: digest(path) for name, path in paths.items()},
    }
    summary["all_development_gates_pass"] = all(summary["gates"].values())
    output = PROJECT / config["output"]
    output.mkdir(parents=True, exist_ok=True)
    (output / "contract.json").write_text(json.dumps(contract, indent=2) + "\n")
    (output / "predictions.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in records)
    )
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
