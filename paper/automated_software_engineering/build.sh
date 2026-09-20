#!/usr/bin/env bash
set -euo pipefail

paper_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$paper_dir"

latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

if rg -i 'undefined refs|undefined citation|overfull|fatal|^! |Difference \(' main.log; then
  echo "Build log contains a blocking warning or error." >&2
  exit 1
fi

pdfinfo main.pdf | rg '^(Pages|Page size|File size)'
