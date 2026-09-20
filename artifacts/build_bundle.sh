#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"
MANIFEST="$PROJECT_ROOT/artifacts/release_manifest.sha256"
ARCHIVE="$PROJECT_ROOT/artifacts/iwcc_reproducibility_bundle.tar.gz"
TEMP_ARCHIVE="$PROJECT_ROOT/artifacts/iwcc_reproducibility_bundle.tmp"

cd "$PROJECT_ROOT"
find . -type f \
  ! -path './.git/*' \
  ! -path './.venv/*' \
  ! -path './.pytest_cache/*' \
  ! -path '*/__pycache__/*' \
  ! -path './submission/*/build/*' \
  ! -path './artifacts/release_manifest.sha256' \
  ! -path './artifacts/*.tar.gz' \
  ! -path './artifacts/*.tmp' \
  ! -name '*.aux' ! -name '*.bbl' ! -name '*.blg' \
  ! -name '*.fdb_latexmk' ! -name '*.fls' ! -name '*.log' \
  ! -name '*.out' ! -name '*.xdv' \
  -print0 | sort -z | xargs -0 sha256sum > "$MANIFEST"

tar -C "$PROJECT_ROOT/.." \
  --exclude="$PROJECT_NAME/.git" \
  --exclude="$PROJECT_NAME/.venv" \
  --exclude="$PROJECT_NAME/.pytest_cache" \
  --exclude='*/__pycache__' \
  --exclude="$PROJECT_NAME/submission/*/build" \
  --exclude="$PROJECT_NAME/artifacts/*.tar.gz" \
  --exclude="$PROJECT_NAME/artifacts/*.tmp" \
  --exclude='*.aux' --exclude='*.bbl' --exclude='*.blg' \
  --exclude='*.fdb_latexmk' --exclude='*.fls' --exclude='*.log' \
  --exclude='*.out' --exclude='*.xdv' \
  -czf "$TEMP_ARCHIVE" "$PROJECT_NAME"
mv "$TEMP_ARCHIVE" "$ARCHIVE"

echo "bundle: $ARCHIVE"
echo "manifest: $MANIFEST"
