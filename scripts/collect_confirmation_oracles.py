#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
import sys
import time

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
from native_common import append, digest, rows


def main() -> None:
    config_path = PROJECT / "configs/confirmation.json"
    config = json.loads(config_path.read_text())
    paper1 = (PROJECT / config["paper1_root"]).resolve()
    sys.path.insert(0, str(paper1 / "revisions/04_state_matched_execution"))
    sys.path.insert(0, str(paper1 / "src"))
    from state_check import PinnedScienceworldSession, validate_jar
    from skilllineage.interactive_envs import AlfworldEpisode

    lock_path = PROJECT / config["outputs"]["method_lock"]
    roster_path = PROJECT / config["outputs"]["roster"]
    lock, roster = json.loads(lock_path.read_text()), json.loads(roster_path.read_text())
    if lock["status"] != "method_frozen_before_confirmation":
        raise RuntimeError("method lock is invalid")
    if roster["status"] != "content_blind_roster_frozen_before_outcomes":
        raise RuntimeError("confirmation roster is invalid")
    jar = paper1 / config["paths"]["scienceworld_jar"]
    validate_jar(jar)
    data_root = Path(os.environ["ALFWORLD_DATA"])
    output = PROJECT / config["outputs"]["oracles"]
    output.mkdir(parents=True, exist_ok=True)
    sources = {
        "config": config_path,
        "method_lock": lock_path,
        "roster": roster_path,
        "collector": Path(__file__),
        "native_common": PROJECT / "scripts/native_common.py",
        "interactive_envs": paper1 / "src/skilllineage/interactive_envs.py",
        "state_check": paper1 / "revisions/04_state_matched_execution/state_check.py",
        "scienceworld_jar": jar,
    }
    tasks = roster["tasks"]
    run_spec = {
        "status": config["status"],
        "tasks": [
            {
                **task,
                **({"gamefile_sha256": digest(data_root / task["task_id"])}
                   if task["environment"] == "alfworld" else {}),
            }
            for task in tasks
        ],
        "input_sha256": {name: digest(path) for name, path in sources.items()},
    }
    run_spec_path = output / "run_spec.json"
    if run_spec_path.exists() and json.loads(run_spec_path.read_text()) != run_spec:
        raise RuntimeError("frozen oracle inputs changed")
    if not run_spec_path.exists():
        if list(output.glob("*.jsonl")):
            raise RuntimeError("cold oracle directory contains unowned evidence")
        run_spec_path.write_text(json.dumps(run_spec, indent=2) + "\n")
    saved = rows(output / "trajectories.jsonl")
    completed = {(row["environment"], row["task_id"]) for row in saved}
    expected = {(row["environment"], row["task_id"]) for row in tasks}
    if len(completed) != len(saved) or not completed <= expected:
        raise RuntimeError("invalid saved oracle records")

    science = PinnedScienceworldSession(max_steps=config["max_steps"]["scienceworld"], jar=jar)
    try:
        for task in tasks:
            key = task["environment"], task["task_id"]
            if key in completed:
                continue
            started, episode = time.perf_counter(), None
            actions, turns, observations = [], [], []
            objective, score, done, error = "", 0.0, False, None
            try:
                if task["environment"] == "alfworld":
                    episode = AlfworldEpisode(
                        data_root / task["task_id"],
                        max_steps=config["max_steps"]["alfworld"], expert=True,
                    )
                else:
                    science.env.load(task["family"], task["variation"], "easy", generateGoldPath=True)
                    if task["variation"] not in list(science.env.get_variations_test()):
                        raise ValueError("ScienceWorld variation is not official TEST")
                    episode = science
                observation, objective, admissible = episode.reset()
                observations.append(observation)
                gold = list(science.env.get_gold_action_sequence()) if task["environment"] == "scienceworld" else None
                for index in range(config["max_steps"][task["environment"]]):
                    action = episode.expert_action() if task["environment"] == "alfworld" else (gold[index] if index < len(gold) else None)
                    if not action:
                        error = "expert/gold actions exhausted before success"
                        break
                    next_observation, score, done, next_actions = episode.step(action)
                    turns.append({
                        "turn": index, "action": action, "admissible_actions": admissible,
                        "listed_admissible": action in admissible, "observation": next_observation,
                        "score": score, "done": done,
                    })
                    actions.append(action)
                    observations.append(next_observation)
                    observation, admissible = next_observation, next_actions
                    if done:
                        break
                if score < 0.999:
                    error = error or "reference did not reach success"
            except Exception as failure:
                error = type(failure).__name__ + ": " + str(failure)
            finally:
                if task["environment"] == "alfworld" and episode is not None:
                    episode.close()
            record = {
                **task, "split": "independent_confirmation", "task_description": objective,
                "executed_actions": actions, "observations": observations, "turns": turns,
                "score": score, "success": score >= 0.999, "done": done, "error": error,
                "unlisted_reference_actions": sum(not row["listed_admissible"] for row in turns),
                "elapsed_seconds": time.perf_counter() - started,
            }
            append(output / "trajectories.jsonl", record)
            completed.add(key)
            print(json.dumps({k: v for k, v in record.items() if k not in {"turns", "observations", "executed_actions"}}), flush=True)
    finally:
        science.close()
    records = rows(output / "trajectories.jsonl")
    if {(row["environment"], row["task_id"]) for row in records} != expected:
        raise RuntimeError("incomplete oracle collection")
    result = {
        "status": "completed", "tasks": len(records),
        "successful_references": sum(row["success"] and not row["error"] for row in records),
        "failed_references": sum(not (row["success"] and not row["error"]) for row in records),
        "by_environment": dict(Counter(row["environment"] for row in records)),
        "by_family_success": {"/".join(key): value for key, value in Counter(
            (row["environment"], row["family"]) for row in records if row["success"] and not row["error"]
        ).items()},
        "unlisted_reference_actions": sum(row["unlisted_reference_actions"] for row in records),
        "trajectories_sha256": digest(output / "trajectories.jsonl"),
    }
    (output / "completion.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
