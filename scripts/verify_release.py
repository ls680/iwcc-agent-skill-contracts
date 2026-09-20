#!/usr/bin/env python3
"""Recompute the frozen primary analysis without changing released outputs."""

from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

from analyze_confirmation import (  # noqa: E402
    metrics,
    percentile,
    permutation_p,
    task_bootstrap,
    task_effects,
)
from native_common import digest, rows  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    config = json.loads((PROJECT / "configs/confirmation.json").read_text())
    lock_path = PROJECT / config["outputs"]["method_lock"]
    lock = json.loads(lock_path.read_text())
    summary_path = PROJECT / config["outputs"]["analysis"] / "summary.json"
    summary = json.loads(summary_path.read_text())

    for relative, expected in lock["file_sha256"].items():
        require(digest(PROJECT / relative) == expected, f"method-lock mismatch: {relative}")

    candidate_dir = PROJECT / config["outputs"]["candidates"]
    public_path = candidate_dir / "public_candidates.jsonl"
    private_path = candidate_dir / "private_labels.jsonl"
    method_path = PROJECT / config["outputs"]["method_results"] / "predictions.jsonl"
    require(digest(lock_path) == summary["input_sha256"]["method_lock"], "summary method-lock hash mismatch")
    require(digest(public_path) == summary["input_sha256"]["public_candidates"], "public candidate hash mismatch")
    require(digest(private_path) == summary["input_sha256"]["private_labels"], "private label hash mismatch")
    require(digest(method_path) == summary["input_sha256"]["program_predictions"], "program prediction hash mismatch")

    public = {row["candidate_id"]: row for row in rows(public_path)}
    private = {row["candidate_id"]: row for row in rows(private_path)}
    method_rows = {row["candidate_id"]: row for row in rows(method_path)}
    require(set(public) == set(private) == set(method_rows), "candidate identifiers differ across released records")

    labels = {key: row["killed"] for key, row in private.items()}
    predictions = {
        name: {key: row["predicted_broken"][name] for key, row in method_rows.items()}
        for name in ("endpoint_only", "ordered_milestones", "iwcc", "nearest_successful_trace")
    }
    for model in json.loads((PROJECT / "configs/models.json").read_text())["models"]:
        label = model["label"]
        response_path = PROJECT / config["outputs"]["llm_results"] / label / "responses.jsonl"
        require(digest(response_path) == summary["input_sha256"][f"llm_{label}"], f"{label} response hash mismatch")
        responses = {row["candidate_id"]: row for row in rows(response_path)}
        require(set(responses) == set(labels), f"{label} candidate identifiers differ")
        predictions[f"llm_{label}"] = {
            key: row["verdict"] == "BROKEN" for key, row in responses.items()
        }

    all_keys = list(labels)
    recomputed_metrics = {
        name: metrics([labels[key] for key in all_keys], [values[key] for key in all_keys])
        for name, values in predictions.items()
    }
    require(recomputed_metrics == summary["metrics"], "released primary metrics do not recompute exactly")

    primary = config["primary_comparator"]
    gain = recomputed_metrics["iwcc"]["balanced_accuracy"] - recomputed_metrics[primary]["balanced_accuracy"]
    require(gain == summary["absolute_gain"], "primary gain mismatch")
    bootstrap = task_bootstrap(
        private,
        labels,
        predictions["iwcc"],
        predictions[primary],
        config["bootstrap_replicates"],
        config["analysis_seed"] + "::bootstrap",
    )
    ci = [percentile(bootstrap, 0.025), percentile(bootstrap, 0.975)]
    require(ci == summary["task_stratified_bootstrap_gain_95_ci"], "bootstrap interval mismatch")
    effects = task_effects(private, labels, predictions["iwcc"], predictions[primary])
    p_value = permutation_p(effects, config["permutation_replicates"], config["analysis_seed"] + "::permutation")
    require(p_value == summary["paired_task_permutation_p"], "paired permutation result mismatch")

    detail_path = PROJECT / config["outputs"]["analysis"] / "predictions_with_private_labels.jsonl"
    require(digest(detail_path) == summary["details_sha256"], "released detail-record hash mismatch")
    audit = json.loads((PROJECT / "research/INFORMATION_BOUNDARY_AUDIT.json").read_text())
    require(audit["status"] == "passed", "information-boundary audit is not passed")
    require(summary["confirmation_passed"], "confirmation status is not passed")
    require(all(summary["confirmation_gates"].values()), "one or more frozen gates failed")
    require(summary["counts"] == {"candidate_programs": 300, "tasks": 60, "killed": 202, "controls": 98}, "unexpected sample counts")

    dependency_jar = PROJECT / "reproduction/workspace_dependencies/01_skilllineage/research/validation/vendor/scienceworld-e8216d6.jar"
    require(digest(dependency_jar) == "e77b0fee7d68abe3ca5b12e57d86e2bfe7603f20c5200da0b0f085939faeb465", "pinned ScienceWorld JAR mismatch")
    for relative in ("paper/en/main.pdf", "paper/zh/main.pdf"):
        path = PROJECT / relative
        require(path.exists() and path.stat().st_size > 50_000, f"missing or implausibly small PDF: {relative}")
        require(path.read_bytes()[:4] == b"%PDF", f"invalid PDF signature: {relative}")

    print(json.dumps({
        "status": "passed",
        "tests": "frozen hashes, record alignment, metrics, bootstrap, permutation, gates, audit, dependencies, PDFs",
        "counts": summary["counts"],
        "iwcc_balanced_accuracy": recomputed_metrics["iwcc"]["balanced_accuracy"],
        "absolute_gain": gain,
        "gain_95_ci": ci,
        "paired_task_permutation_p": p_value,
    }, indent=2))


if __name__ == "__main__":
    main()
