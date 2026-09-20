#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
sha256sum --check artifacts/release_manifest.sha256
gzip --test artifacts/iwcc_reproducibility_bundle.tar.gz
tar -tzf artifacts/iwcc_reproducibility_bundle.tar.gz >/dev/null
echo "release manifest and archive passed"
