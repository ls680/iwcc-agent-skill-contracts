#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
from native_common import digest


def rank(task: dict, seed: str) -> str:
    text = f"{seed}:{task['environment']}:{task['family']}:{task['task_id']}"
    return hashlib.sha256(text.encode()).hexdigest()


def main() -> None:
    config_path = PROJECT / "configs/confirmation.json"
    config = json.loads(config_path.read_text())
    paper1 = (PROJECT / config["paper1_root"]).resolve()
    paper3 = (PROJECT / config["paper3_root"]).resolve()
    paper4 = (PROJECT / config["paper4_root"]).resolve()
    lock_path = PROJECT / config["outputs"]["method_lock"]
    if json.loads(lock_path.read_text())["status"] != "method_frozen_before_confirmation":
        raise RuntimeError("method is not frozen")
    paths = {name: paper1 / value for name, value in config["paths"].items()}
    used_sources = [
        paths["r22_run_spec"],
        paths["r23_roster"],
        paths["r24_roster"],
        paper3 / config["prior_rosters"]["paper3"],
        paper4 / config["prior_rosters"]["paper4"],
    ]
    used = set()
    for path in used_sources:
        artifact = json.loads(path.read_text())
        used.update(
            (row["environment"], row["task_id"])
            for row in artifact["tasks"]
        )
    inventory = json.loads(paths["inventory"].read_text())
    snapshot = json.loads(paths["reserved_snapshot"].read_text())
    selected = []
    for family in config["alfworld_families"]:
        candidates = [
            task for task in inventory["tasks"]
            if task["environment"] == "alfworld"
            and task["family"] == family
            and task["official_split"] in config["alfworld_official_splits"]
            and task["compatible_with_original_scope"]
            and ("alfworld", task["task_id"]) not in used
        ]
        quota = config["alfworld_tasks_by_family"][family]
        chosen = sorted(candidates, key=lambda row: rank(row, config["selection_seed"]))[:quota]
        if len(chosen) != quota:
            raise RuntimeError(f"insufficient untouched ALFWorld tasks for {family}")
        selected.extend(chosen)
    for family in config["scienceworld_families"]:
        candidates = [
            task for task in snapshot["reserved_test_pool"]
            if task["environment"] == "scienceworld"
            and task["family"] == family
            and task["compatible_with_original_scope"]
            and ("scienceworld", task["task_id"]) not in used
        ]
        chosen = sorted(candidates, key=lambda row: rank(row, config["selection_seed"]))[
            : config["scienceworld_tasks_per_family"]
        ]
        if len(chosen) != config["scienceworld_tasks_per_family"]:
            raise RuntimeError(f"insufficient untouched ScienceWorld tasks for {family}")
        selected.extend(chosen)
    keys = {(row["environment"], row["task_id"]) for row in selected}
    if len(keys) != len(selected) or keys & used:
        raise RuntimeError("confirmation roster overlaps prior evidence")
    artifact = {
        "status": "content_blind_roster_frozen_before_outcomes",
        "selection_uses_only": [
            "environment", "family", "task_id", "official_split",
            "compatibility flag", "prior-exposure exclusion",
        ],
        "selection_seed": config["selection_seed"],
        "tasks": selected,
        "task_count": len(selected),
        "by_environment": dict(Counter(row["environment"] for row in selected)),
        "families": len({(row["environment"], row["family"]) for row in selected}),
        "overlap_with_prior_evidence": 0,
        "input_sha256": {
            "config": digest(config_path),
            "method_lock": digest(lock_path),
            "inventory": digest(paths["inventory"]),
            "reserved_snapshot": digest(paths["reserved_snapshot"]),
            **{f"used_source_{index}": digest(path) for index, path in enumerate(used_sources, 1)},
            "script": digest(Path(__file__)),
        },
    }
    output = PROJECT / config["outputs"]["roster"]
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and json.loads(output.read_text()) != artifact:
        raise RuntimeError("frozen roster changed")
    output.write_text(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps({key: artifact[key] for key in ("status", "task_count", "by_environment", "families")}, indent=2))


if __name__ == "__main__":
    main()
