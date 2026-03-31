#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

CHANNEL_ID="${1:-ricce-ontology-preview}"

if rg -n 'replace-with-your-firebase-project-id' .firebaserc >/dev/null; then
  printf '[FAIL] Replace the placeholder Firebase project ID in .firebaserc before running a preview deploy.\n' >&2
  printf 'Tip: ./scripts/set_firebase_project.sh <your-project-id>\n' >&2
  exit 1
fi

./scripts/security-checks.sh
firebase hosting:channel:deploy "$CHANNEL_ID"
