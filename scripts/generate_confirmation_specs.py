#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
sys.path.insert(0, str(PROJECT / "src"))
from iwcc.actions import parse_action, role_name
from native_common import digest, rows


def seeded_index(record: dict, operator: str, seed: str) -> int | None:
    actions, turns = record["executed_actions"], record["turns"]
    if len(actions) < 2:
        return None
    if operator == "truncate_suffix":
        return max(1, len(actions) - 3)
    stop = len(actions) - 1 if operator == "adjacent_order_swap" else len(actions)
    candidates = [
        index for index in range(max(1, len(actions) - 6), stop)
        if actions[index] in turns[index]["admissible_actions"]
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda index: hashlib.sha256(
        f"{seed}|{record['environment']}|{record['task_id']}|{operator}|{index}".encode()
    ).hexdigest())


def role_substitution(record: dict) -> tuple[int, str] | None:
    for index in range(len(record["executed_actions"]) - 1, -1, -1):
        action = record["executed_actions"][index]
        event = parse_action(action)
        if event.operator == "use":
            return index, "use floorlamp 1"
        if event.operator != "place":
            continue
        if record["environment"] == "scienceworld":
            colors = ["red", "green", "blue", "yellow", "orange", "purple"]
            match = re.search(r"\b(" + "|".join(colors) + r") box$", event.target)
            current = match.group(1) if match else "red"
            replacement = colors[(colors.index(current) + 1) % len(colors)]
            return index, f"move {event.subject} to {replacement} box"
        for target in ("garbagecan 1", "countertop 1", "cabinet 1", "drawer 1", "shelf 1"):
            if role_name(target) != role_name(event.target):
                return index, f"move {event.subject} to {target}"
    return None


def main() -> None:
    config_path = PROJECT / "configs/confirmation.json"
    config = json.loads(config_path.read_text())
    oracle_dir = PROJECT / config["outputs"]["oracles"]
    completion = json.loads((oracle_dir / "completion.json").read_text())
    if completion["status"] != "completed":
        raise RuntimeError("confirmation oracles are incomplete")
    records = [row for row in rows(oracle_dir / "trajectories.jsonl") if row["success"] and not row["error"]]
    specs = []
    for record in records:
        for operator in config["operators"]:
            replacement_action = None
            if operator == "role_substitution":
                selected = role_substitution(record)
                if selected is None:
                    continue
                index, replacement_action = selected
                rule = "replace final objective-bearing action with a fixed wrong role"
            else:
                index = seeded_index(record, operator, config["mutation_seed"])
                if index is None:
                    continue
                rule = "three-action tail truncation" if operator == "truncate_suffix" else "seeded admissible index within final six healthy actions"
            payload = f"{record['environment']}|{record['task_id']}|{operator}|{index}|{replacement_action or ''}"
            specs.append({
                "spec_id": hashlib.sha256(payload.encode()).hexdigest()[:20],
                "environment": record["environment"], "family": record["family"],
                "task_id": record["task_id"], "operator": operator,
                "program_index": index, "replacement_action": replacement_action,
                "selection_rule": rule,
            })
    artifact = {
        "status": "mutation_specs_frozen_before_outcomes",
        "generation_reads_mutation_outcomes": False,
        "mutation_seed": config["mutation_seed"], "specs": specs,
        "spec_count": len(specs),
        "by_environment": dict(Counter(row["environment"] for row in specs)),
        "by_operator": dict(Counter(row["operator"] for row in specs)),
        "input_sha256": {
            "config": digest(config_path),
            "method_lock": digest(PROJECT / config["outputs"]["method_lock"]),
            "roster": digest(PROJECT / config["outputs"]["roster"]),
            "oracle_completion": digest(oracle_dir / "completion.json"),
            "oracle_trajectories": digest(oracle_dir / "trajectories.jsonl"),
            "generator": digest(Path(__file__)),
        },
    }
    output = PROJECT / config["outputs"]["mutation_specs"]
    if output.exists() and json.loads(output.read_text()) != artifact:
        raise RuntimeError("frozen mutation specifications changed")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps({key: artifact[key] for key in ("status", "spec_count", "by_environment", "by_operator")}, indent=2))


if __name__ == "__main__":
    main()
