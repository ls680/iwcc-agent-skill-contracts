#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


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


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    config = json.loads((PROJECT / "configs/development_v2.json").read_text())
    paper4 = (PROJECT / config["paper4_root"]).resolve()
    oracle_path = paper4 / config["inputs"]["oracles"]
    outcome_path = paper4 / config["inputs"]["mutation_outcomes"]
    traces = [row for row in rows(oracle_path) if row["success"] and not row["error"]]
    by_task = {(row["environment"], row["task_id"]): row for row in traces}
    outcomes = [row for row in rows(outcome_path) if not row["technical_error"]]
    public, private = [], []
    for trace in traces:
        candidate_id = hashlib.sha256(
            f"healthy|{trace['environment']}|{trace['task_id']}".encode()
        ).hexdigest()[:20]
        public.append(
            {
                "candidate_id": candidate_id,
                "environment": trace["environment"],
                "family": trace["family"],
                "objective": trace["task_description"],
                "initial_observation": trace["observations"][0],
                "program": trace["executed_actions"],
            }
        )
        private.append(
            {
                "candidate_id": candidate_id,
                "killed": False,
                "kind": "healthy",
                "environment": trace["environment"],
                "family": trace["family"],
                "task_id": trace["task_id"],
            }
        )
    for outcome in outcomes:
        trace = by_task[(outcome["environment"], outcome["task_id"])]
        public.append(
            {
                "candidate_id": outcome["spec_id"],
                "environment": outcome["environment"],
                "family": outcome["family"],
                "objective": trace["task_description"],
                "initial_observation": trace["observations"][0],
                "program": mutate(
                    trace["executed_actions"], outcome["operator"], outcome["program_index"]
                ),
            }
        )
        private.append(
            {
                "candidate_id": outcome["spec_id"],
                "killed": outcome["killed"],
                "kind": "mutation",
                "operator": outcome["operator"],
                "program_index": outcome["program_index"],
                "environment": outcome["environment"],
                "family": outcome["family"],
                "task_id": outcome["task_id"],
            }
        )
    output = PROJECT / "data/development"
    output.mkdir(parents=True, exist_ok=True)
    public_path = output / "public_candidates.jsonl"
    private_path = output / "private_labels.jsonl"
    public_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in public))
    private_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in private))
    metadata = {
        "status": "exposed_development_candidates",
        "candidates": len(public),
        "public_contains_native_outcome": False,
        "private_labels_are_forbidden_to_judges": True,
        "input_sha256": {"oracles": digest(oracle_path), "outcomes": digest(outcome_path)},
        "output_sha256": {"public": digest(public_path), "private": digest(private_path)},
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
