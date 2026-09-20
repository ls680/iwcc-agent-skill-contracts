#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import time

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
from native_common import append, digest, rows


def state_signature(observation: str, objective: str, actions: list[str]) -> str:
    return hashlib.sha256(json.dumps(
        {"observation": observation, "objective": objective, "actions": actions},
        ensure_ascii=False, sort_keys=True,
    ).encode()).hexdigest()


def mutate(actions: list[str], spec: dict) -> list[str]:
    candidate, index = list(actions), spec["program_index"]
    if spec["operator"] == "delete_action":
        del candidate[index]
    elif spec["operator"] == "adjacent_order_swap":
        candidate[index], candidate[index + 1] = candidate[index + 1], candidate[index]
    elif spec["operator"] == "truncate_suffix":
        candidate = candidate[:index]
    elif spec["operator"] == "role_substitution":
        candidate[index] = spec["replacement_action"]
    else:
        raise ValueError(spec["operator"])
    return candidate


def main() -> None:
    config_path = PROJECT / "configs/confirmation.json"
    config = json.loads(config_path.read_text())
    paper1 = (PROJECT / config["paper1_root"]).resolve()
    sys.path.insert(0, str(paper1 / "revisions/04_state_matched_execution"))
    sys.path.insert(0, str(paper1 / "src"))
    from state_check import PinnedScienceworldSession
    from skilllineage.interactive_envs import AlfworldEpisode

    oracle_dir = PROJECT / config["outputs"]["oracles"]
    oracles = {(row["environment"], row["task_id"]): row for row in rows(
        oracle_dir / "trajectories.jsonl"
    ) if row["success"] and not row["error"]}
    spec_path = PROJECT / config["outputs"]["mutation_specs"]
    artifact = json.loads(spec_path.read_text())
    if artifact["status"] != "mutation_specs_frozen_before_outcomes":
        raise RuntimeError("mutation specifications are not frozen")
    output = PROJECT / config["outputs"]["mutations"]
    output.mkdir(parents=True, exist_ok=True)
    run_spec = {
        "status": "independent_confirmation_native_mutations",
        "planned_specs": [row["spec_id"] for row in artifact["specs"]],
        "input_sha256": {name: digest(path) for name, path in {
            "config": config_path, "method_lock": PROJECT / config["outputs"]["method_lock"],
            "roster": PROJECT / config["outputs"]["roster"], "mutation_specs": spec_path,
            "oracles": oracle_dir / "trajectories.jsonl", "runner": Path(__file__),
        }.items()},
    }
    run_spec_path = output / "run_spec.json"
    if run_spec_path.exists() and json.loads(run_spec_path.read_text()) != run_spec:
        raise RuntimeError("frozen mutation inputs changed")
    if not run_spec_path.exists():
        if list(output.glob("*.jsonl")):
            raise RuntimeError("cold mutation directory contains unowned evidence")
        run_spec_path.write_text(json.dumps(run_spec, indent=2) + "\n")
    outcome_path = output / "outcomes.jsonl"
    saved = rows(outcome_path)
    completed = {row["spec_id"] for row in saved}
    if len(saved) != len(completed):
        raise RuntimeError("duplicate mutation outcomes")
    science = PinnedScienceworldSession(
        max_steps=config["max_steps"]["scienceworld"],
        jar=paper1 / config["paths"]["scienceworld_jar"],
    )
    try:
        for spec in artifact["specs"]:
            if spec["spec_id"] in completed:
                continue
            record = oracles[(spec["environment"], spec["task_id"])]
            started, episode = time.perf_counter(), None
            turns, error, score, done, initial_match = [], None, 0.0, False, False
            try:
                if spec["environment"] == "alfworld":
                    episode = AlfworldEpisode(Path(os.environ["ALFWORLD_DATA"]) / spec["task_id"], max_steps=config["max_steps"]["alfworld"], expert=False)
                else:
                    science.configure(spec["family"], record["variation"], "easy")
                    episode = science
                observation, objective, admissible = episode.reset()
                expected = state_signature(record["observations"][0], record["task_description"], record["turns"][0]["admissible_actions"])
                initial_match = state_signature(observation, objective, admissible) == expected
                if not initial_match:
                    raise RuntimeError("mutation initial state mismatch")
                candidate = mutate(record["executed_actions"], spec)
                for program_index, action in enumerate(candidate):
                    if done:
                        break
                    next_observation, score, done, next_actions = episode.step(action)
                    turns.append({
                        "program_index": program_index, "action": action,
                        "listed_admissible": action in admissible, "observation": next_observation,
                        "score": score, "done": done,
                    })
                    observation, admissible = next_observation, next_actions
            except Exception as failure:
                error = type(failure).__name__ + ": " + str(failure)
            finally:
                if spec["environment"] == "alfworld" and episode is not None:
                    episode.close()
            outcome = {
                **spec, "healthy_success": True, "initial_state_match": initial_match,
                "candidate_program": mutate(record["executed_actions"], spec),
                "turns": turns, "score": score, "done": done, "success": score >= 0.999,
                "killed": score < 0.999 if error is None else None,
                "technical_error": error, "elapsed_seconds": time.perf_counter() - started,
            }
            append(outcome_path, outcome)
            completed.add(spec["spec_id"])
            print(json.dumps({k: v for k, v in outcome.items() if k not in {"turns", "candidate_program"}}), flush=True)
    finally:
        science.close()
    outcomes = rows(outcome_path)
    if len(outcomes) != len(artifact["specs"]):
        raise RuntimeError("mutation confirmation incomplete")
    result = {
        "status": "completed" if not any(row["technical_error"] for row in outcomes) else "invalid_technical_errors",
        "native_replays": len(outcomes), "killed_incidents": sum(row["killed"] is True for row in outcomes),
        "surviving_mutations": sum(row["killed"] is False for row in outcomes),
        "technical_errors": sum(bool(row["technical_error"]) for row in outcomes),
        "initial_state_matches": sum(row["initial_state_match"] for row in outcomes),
        "by_environment": dict(Counter(row["environment"] for row in outcomes)),
        "by_operator": dict(Counter(row["operator"] for row in outcomes)),
        "outcomes_sha256": digest(outcome_path),
    }
    (output / "completion.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
