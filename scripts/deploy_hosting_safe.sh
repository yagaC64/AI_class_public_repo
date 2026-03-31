#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if rg -n 'replace-with-your-firebase-project-id' .firebaserc >/dev/null; then
  printf '[FAIL] Replace the placeholder Firebase project ID in .firebaserc before deploying.\n' >&2
  exit 1
fi

./scripts/security-checks.sh
firebase deploy --only hosting "$@"
