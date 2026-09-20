#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ -z "${ALFWORLD_DATA:-}" || ! -d "$ALFWORLD_DATA" ]]; then
  echo "ALFWORLD_DATA must name the installed ALFWorld game-data directory" >&2
  exit 2
fi

python scripts/freeze_confirmation_roster.py
python scripts/collect_confirmation_oracles.py
python scripts/generate_confirmation_specs.py
python scripts/run_confirmation_mutations.py
python scripts/build_confirmation_candidates.py
python scripts/run_program_validators.py
python scripts/run_llm_judge.py --split confirmation --model-label qwen3_4b
python scripts/run_llm_judge.py --split confirmation --model-label phi4_mini
python scripts/run_llm_judge.py --split confirmation --model-label mistral7b_v03
python scripts/audit_information_boundary.py
python scripts/analyze_confirmation.py
python scripts/benchmark_and_summarize.py

echo "native confirmation complete: results/confirmation/final/summary.json"
