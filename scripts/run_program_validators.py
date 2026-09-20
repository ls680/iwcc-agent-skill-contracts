#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
sys.path.insert(0, str(PROJECT / "src"))
from iwcc.actions import parse_action
from iwcc.validator import validate_program
from native_common import digest, rows


def edit_distance(left: list[str], right: list[str]) -> int:
    previous = list(range(len(right) + 1))
    for index, lvalue in enumerate(left, 1):
        current = [index]
        for jndex, rvalue in enumerate(right, 1):
            current.append(min(current[-1] + 1, previous[jndex] + 1, previous[jndex - 1] + int(lvalue != rvalue)))
        previous = current
    return previous[-1]


def operators(program: list[str]) -> list[str]:
    return [parse_action(action).operator for action in program]


def main() -> None:
    config_path = PROJECT / "configs/confirmation.json"
    config = json.loads(config_path.read_text())
    public_path = PROJECT / config["outputs"]["candidates"] / "public_candidates.jsonl"
    contract_path = PROJECT / config["frozen_contract"]
    development_public = PROJECT / "data/development/public_candidates.jsonl"
    development_labels = PROJECT / "data/development/private_labels.jsonl"
    output = PROJECT / config["outputs"]["method_results"]
    output.mkdir(parents=True, exist_ok=True)
    run_spec = {
        "status": "confirmation_program_validators_frozen_inputs",
        "confirmation_private_labels_opened": False,
        "nearest_threshold": config["nearest_successful_trace_threshold"],
        "input_sha256": {
            "config": digest(config_path), "method_lock": digest(PROJECT / config["outputs"]["method_lock"]),
            "public_candidates": digest(public_path), "contract": digest(contract_path),
            "development_public": digest(development_public), "development_labels": digest(development_labels),
            "runner": digest(Path(__file__)),
        },
    }
    spec_path = output / "run_spec.json"
    if spec_path.exists() and json.loads(spec_path.read_text()) != run_spec:
        raise RuntimeError("program-validator inputs changed")
    if not spec_path.exists():
        spec_path.write_text(json.dumps(run_spec, indent=2) + "\n")
    candidates, contract = rows(public_path), json.loads(contract_path.read_text())
    dev_labels = {row["candidate_id"]: row for row in rows(development_labels)}
    references: dict[tuple[str, str], list[list[str]]] = defaultdict(list)
    for row in rows(development_public):
        if not dev_labels[row["candidate_id"]]["killed"]:
            references[(row["environment"], row["family"])].append(operators(row["program"]))
    results = []
    for candidate in candidates:
        decisions, violations = {}, {}
        for mode in ("endpoint_only", "ordered_milestones", "iwcc"):
            result = validate_program(
                contract, environment=candidate["environment"], family=candidate["family"],
                objective=candidate["objective"], program=candidate["program"], mode=mode,
                initial_observation=candidate["initial_observation"],
            )
            decisions[mode] = not result["valid"]
            violations[mode] = result["violations"]
        sequence = operators(candidate["program"])
        pool = references[(candidate["environment"], candidate["family"])]
        nearest = min(edit_distance(sequence, reference) / max(len(sequence), len(reference), 1) for reference in pool)
        decisions["nearest_successful_trace"] = nearest > config["nearest_successful_trace_threshold"]
        results.append({
            "candidate_id": candidate["candidate_id"], "predicted_broken": decisions,
            "violations": violations, "nearest_score": nearest,
        })
    result_path = output / "predictions.jsonl"
    result_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in results))
    completion = {
        "status": "completed", "candidates": len(results),
        "confirmation_private_labels_opened": False,
        "predictions_sha256": digest(result_path),
    }
    (output / "completion.json").write_text(json.dumps(completion, indent=2) + "\n")
    print(json.dumps(completion, indent=2))


if __name__ == "__main__":
    main()
