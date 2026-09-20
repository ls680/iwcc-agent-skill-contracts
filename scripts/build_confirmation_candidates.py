#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
from native_common import digest, rows


def main() -> None:
    config_path = PROJECT / "configs/confirmation.json"
    config = json.loads(config_path.read_text())
    oracle_dir = PROJECT / config["outputs"]["oracles"]
    mutation_dir = PROJECT / config["outputs"]["mutations"]
    if json.loads((mutation_dir / "completion.json").read_text())["status"] != "completed":
        raise RuntimeError("native mutation evidence is incomplete")
    traces = [row for row in rows(oracle_dir / "trajectories.jsonl") if row["success"] and not row["error"]]
    outcomes = [row for row in rows(mutation_dir / "outcomes.jsonl") if not row["technical_error"]]
    public, private = [], []
    for trace in traces:
        candidate_id = hashlib.sha256(f"healthy|{trace['environment']}|{trace['task_id']}".encode()).hexdigest()[:20]
        public.append({
            "candidate_id": candidate_id, "environment": trace["environment"],
            "family": trace["family"], "objective": trace["task_description"],
            "initial_observation": trace["observations"][0], "program": trace["executed_actions"],
        })
        private.append({
            "candidate_id": candidate_id, "killed": False, "kind": "healthy",
            "environment": trace["environment"], "family": trace["family"], "task_id": trace["task_id"],
        })
    for outcome in outcomes:
        trace = next(row for row in traces if row["environment"] == outcome["environment"] and row["task_id"] == outcome["task_id"])
        public.append({
            "candidate_id": outcome["spec_id"], "environment": outcome["environment"],
            "family": outcome["family"], "objective": trace["task_description"],
            "initial_observation": trace["observations"][0], "program": outcome["candidate_program"],
        })
        private.append({
            "candidate_id": outcome["spec_id"], "killed": outcome["killed"], "kind": "mutation",
            "operator": outcome["operator"], "program_index": outcome["program_index"],
            "environment": outcome["environment"], "family": outcome["family"], "task_id": outcome["task_id"],
        })
    output = PROJECT / config["outputs"]["candidates"]
    output.mkdir(parents=True, exist_ok=True)
    public_path, private_path = output / "public_candidates.jsonl", output / "private_labels.jsonl"
    public_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in public))
    private_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in private))
    metadata = {
        "status": "confirmation_candidates_built_after_native_outcomes",
        "candidates": len(public), "killed": sum(row["killed"] for row in private),
        "controls": sum(not row["killed"] for row in private),
        "public_contains_native_outcome": False,
        "public_contains_task_locator": False,
        "private_labels_are_forbidden_to_judges": True,
        "input_sha256": {"oracles": digest(oracle_dir / "trajectories.jsonl"), "outcomes": digest(mutation_dir / "outcomes.jsonl")},
        "output_sha256": {"public": digest(public_path), "private": digest(private_path)},
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
