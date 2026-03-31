#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -f data/private/ricce-ontology-master.csv ]]; then
  printf '[FAIL] Missing private master CSV: data/private/ricce-ontology-master.csv\n' >&2
  exit 1
fi

python3 scripts/prepare_public_data.py "$@"
./scripts/security-checks.sh

printf '\nLocal private-preview dataset is current and excluded from Firebase Hosting.\n'
printf 'Preview CSV: public/data/local/ricce-ontology-private-preview.csv\n'
printf 'Manifest: public/data/local/ricce-ontology-private-preview.manifest.json\n'
