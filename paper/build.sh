#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "${PROJECT_ROOT}/scripts/render_paper_assets.py"
for language in en zh; do
  (
    cd "${PROJECT_ROOT}/paper/${language}"
    latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
  )
done
for language in en zh; do
  log="${PROJECT_ROOT}/paper/${language}/main.log"
  if grep -Eq "Undefined control sequence|LaTeX Warning:.*undefined|Overfull \\hbox" "${log}"; then
    echo "paper validation failed: ${log}" >&2
    exit 1
  fi
done
