#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
from native_common import digest


def main() -> None:
    config_path = PROJECT / "configs/confirmation.json"
    config = json.loads(config_path.read_text())
    output = PROJECT / config["outputs"]["method_lock"]
    forbidden = [
        PROJECT / config["outputs"][name]
        for name in (
            "roster", "oracles", "mutation_specs", "mutations", "candidates",
            "method_results", "llm_results", "analysis",
        )
    ]
    if not output.exists() and any(path.exists() for path in forbidden):
        raise RuntimeError("confirmation artifact exists before method freeze")
    frozen = [
        config_path,
        PROJECT / "configs/models.json",
        PROJECT / "research/PROTOCOL.md",
        PROJECT / "results/development/v2/contract.json",
        PROJECT / "results/development/final/summary.json",
        *sorted((PROJECT / "src/iwcc").glob("*.py")),
        *sorted((PROJECT / "tests").glob("test_*.py")),
        *sorted((PROJECT / "scripts").glob("*.py")),
    ]
    artifact = {
        "status": "method_frozen_before_confirmation",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "confirmation_outcomes_seen": False,
        "primary_comparator": config["primary_comparator"],
        "gates": config["gates"],
        "file_sha256": {
            str(path.relative_to(PROJECT)): digest(path)
            for path in frozen
            if path != Path(__file__)
        },
    }
    artifact["file_sha256"][str(Path(__file__).relative_to(PROJECT))] = digest(Path(__file__))
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        existing = json.loads(output.read_text())
        comparable = dict(existing)
        comparable["frozen_at_utc"] = artifact["frozen_at_utc"]
        if comparable != artifact:
            raise RuntimeError("frozen method files changed")
        print(json.dumps(existing, indent=2))
        return
    output.write_text(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps(artifact, indent=2))


if __name__ == "__main__":
    main()
