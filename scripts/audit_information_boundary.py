#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
RUNNERS = ("scripts/run_program_validators.py", "scripts/run_llm_judge.py")
FORBIDDEN_PUBLIC_KEYS = {"task_id", "variation", "killed", "success", "score", "operator", "program_index"}


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def main() -> None:
    config = json.loads((PROJECT / "configs/confirmation.json").read_text())
    public = PROJECT / config["outputs"]["candidates"] / "public_candidates.jsonl"
    source_violations = []
    for relative in RUNNERS:
        text = (PROJECT / relative).read_text()
        if "data/confirmation/private_labels.jsonl" in text:
            source_violations.append({"runner": relative, "marker": "confirmation private labels"})
    public_violations = []
    for line, row in enumerate(rows(public), 1):
        forbidden = sorted(set(row) & FORBIDDEN_PUBLIC_KEYS)
        if forbidden:
            public_violations.append({"line": line, "keys": forbidden})
    run_spec_violations = []
    for path in [
        PROJECT / config["outputs"]["method_results"] / "run_spec.json",
        *(PROJECT / config["outputs"]["llm_results"]).glob("*/run_spec.json"),
    ]:
        spec = json.loads(path.read_text())
        flag = spec.get("confirmation_private_labels_opened", spec.get("private_labels_opened"))
        if flag is not False:
            run_spec_violations.append(str(path.relative_to(PROJECT)))
    audit = {
        "status": "passed" if not (source_violations or public_violations or run_spec_violations) else "failed",
        "runners": list(RUNNERS), "source_violations": source_violations,
        "public_key_violations": public_violations, "run_spec_violations": run_spec_violations,
        "interpretation": "Native outcomes and task locators are unavailable to all pre-execution judges; only the post-hoc analyzer opens private labels.",
    }
    output = PROJECT / "research/INFORMATION_BOUNDARY_AUDIT.json"
    output.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))
    if audit["status"] != "passed":
        raise RuntimeError("information-boundary audit failed")


if __name__ == "__main__":
    main()
