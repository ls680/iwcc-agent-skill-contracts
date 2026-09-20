#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
import json
from math import sqrt
from pathlib import Path
import statistics
import sys
import time

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
sys.path.insert(0, str(PROJECT / "src"))
from iwcc.validator import validate_program
from native_common import digest, rows


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    position = p * (len(ordered) - 1)
    lower, upper = int(position), min(int(position) + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def wilson(successes: int, trials: int, z: float = 1.959963984540054) -> list[float]:
    center = (successes + z * z / 2) / (trials + z * z)
    half = z * sqrt(successes * (trials - successes) / trials + z * z / 4) / (trials + z * z)
    return [center - half, center + half]


def main() -> None:
    config = json.loads((PROJECT / "configs/confirmation.json").read_text())
    candidate_dir = PROJECT / config["outputs"]["candidates"]
    public = rows(candidate_dir / "public_candidates.jsonl")
    private = {row["candidate_id"]: row for row in rows(candidate_dir / "private_labels.jsonl")}
    contract_path = PROJECT / config["frozen_contract"]
    contract = json.loads(contract_path.read_text())
    predictions_path = PROJECT / config["outputs"]["method_results"] / "predictions.jsonl"
    predictions = {row["candidate_id"]: row for row in rows(predictions_path)}

    timings = []
    repeats = 100
    for _ in range(3):
        for row in public:
            validate_program(contract, environment=row["environment"], family=row["family"], objective=row["objective"], program=row["program"], initial_observation=row["initial_observation"])
    started = time.perf_counter()
    for _ in range(repeats):
        for row in public:
            tick = time.perf_counter_ns()
            validate_program(contract, environment=row["environment"], family=row["family"], objective=row["objective"], program=row["program"], initial_observation=row["initial_observation"])
            timings.append((time.perf_counter_ns() - tick) / 1e6)
    elapsed = time.perf_counter() - started

    detected = []
    for candidate_id, label in private.items():
        if not label["killed"] or not predictions[candidate_id]["predicted_broken"]["iwcc"]:
            continue
        target = label.get("program_index")
        indices = [row["index"] for row in predictions[candidate_id]["violations"]["iwcc"]]
        detected.append({
            "exact": target is not None and target in indices,
            "within_one": target is not None and any(abs(target - index) <= 1 for index in indices),
        })
    summary = json.loads((PROJECT / config["outputs"]["analysis"] / "summary.json").read_text())
    by_family = summary["by_family"]
    family_directions = [
        group["iwcc"]["balanced_accuracy"] - group[config["primary_comparator"]]["balanced_accuracy"]
        for group in by_family.values()
    ]
    contract_clauses = sum(
        len(item["required_milestones"]) + len(item["precedence"])
        for item in contract["contracts"].values()
    ) + len(contract["navigation_edges"])
    llm_completion = {
        model["label"]: json.loads((PROJECT / config["outputs"]["llm_results"] / model["label"] / "completion.json").read_text())
        for model in json.loads((PROJECT / "configs/models.json").read_text())["models"]
    }
    result = {
        "status": "posthoc_descriptive_secondary_analysis",
        "primary_confirmation_unchanged": True,
        "runtime": {
            "device": "single CPU process",
            "candidate_validations": len(timings),
            "repeats": repeats,
            "median_milliseconds": statistics.median(timings),
            "p95_milliseconds": percentile(timings, 0.95),
            "throughput_programs_per_second": len(timings) / elapsed,
        },
        "contract": {
            "successful_development_trace_witnesses": contract["trace_count"],
            "family_contracts": len(contract["contracts"]),
            "required_and_precedence_plus_navigation_clauses": contract_clauses,
            "navigation_edges": len(contract["navigation_edges"]),
            "canonical_sha256": contract["canonical_sha256"],
        },
        "localization_among_detected_kills": {
            "detected": len(detected),
            "exact_rate": sum(row["exact"] for row in detected) / len(detected),
            "within_one_rate": sum(row["within_one"] for row in detected) / len(detected),
        },
        "uncertainty": {
            "killed_recall_wilson_95_ci": wilson(summary["metrics"]["iwcc"]["true_positive"], summary["counts"]["killed"]),
            "zero_false_rejection_wilson_95_upper": wilson(summary["metrics"]["iwcc"]["false_positive"], summary["counts"]["controls"])[1],
        },
        "family_directions": {
            "positive": sum(value > 0 for value in family_directions),
            "tied": sum(value == 0 for value in family_directions),
            "negative": sum(value < 0 for value in family_directions),
        },
        "gpu_judges": {
            label: {
                "candidates": row["candidates"],
                "peak_cuda_memory_gib": row["peak_cuda_memory_gib"],
                "elapsed_seconds": row["elapsed_seconds_this_process"],
            }
            for label, row in llm_completion.items()
        },
        "input_sha256": {
            "public": digest(candidate_dir / "public_candidates.jsonl"),
            "private": digest(candidate_dir / "private_labels.jsonl"),
            "contract": digest(contract_path),
            "predictions": digest(predictions_path),
            "primary_summary": digest(PROJECT / config["outputs"]["analysis"] / "summary.json"),
        },
    }
    output = PROJECT / config["outputs"]["analysis"] / "secondary_metrics.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
