#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 /path/to/new-empty-workspace" >&2
  exit 2
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DESTINATION="$(realpath -m "$1")"
if [[ -e "$DESTINATION" ]]; then
  echo "destination already exists; choose a new path: $DESTINATION" >&2
  exit 2
fi
case "$DESTINATION" in
  /|"$PROJECT_ROOT"|"$PROJECT_ROOT"/*)
    echo "destination must be a new directory outside the repository" >&2
    exit 2
    ;;
esac

mkdir -p "$DESTINATION/05_witnessed_contracts/data" "$DESTINATION/05_witnessed_contracts/results" "$DESTINATION/05_witnessed_contracts/reproduction"
cp -a "$PROJECT_ROOT/reproduction/workspace_dependencies/." "$DESTINATION/"
cp -a "$PROJECT_ROOT/configs" "$DESTINATION/05_witnessed_contracts/"
cp -a "$PROJECT_ROOT/src" "$DESTINATION/05_witnessed_contracts/"
cp -a "$PROJECT_ROOT/scripts" "$DESTINATION/05_witnessed_contracts/"
cp -a "$PROJECT_ROOT/tests" "$DESTINATION/05_witnessed_contracts/"
cp -a "$PROJECT_ROOT/research" "$DESTINATION/05_witnessed_contracts/"
cp -a "$PROJECT_ROOT/data/development" "$DESTINATION/05_witnessed_contracts/data/"
cp -a "$PROJECT_ROOT/results/development" "$DESTINATION/05_witnessed_contracts/results/"
cp -a "$PROJECT_ROOT/environment" "$DESTINATION/05_witnessed_contracts/"
cp -a "$PROJECT_ROOT/reproduction/run_native_confirmation.sh" "$DESTINATION/05_witnessed_contracts/reproduction/"
cp -a "$PROJECT_ROOT/pyproject.toml" "$DESTINATION/05_witnessed_contracts/"

echo "clean native-reproduction workspace prepared at: $DESTINATION"
