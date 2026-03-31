#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ $# -lt 1 ]]; then
  printf 'Usage: %s <firebase-project-id>\n' "$0" >&2
  exit 1
fi

PROJECT_ID="$1"

if [[ ! "$PROJECT_ID" =~ ^[a-z0-9-]{6,30}$ ]]; then
  printf '[FAIL] Firebase project IDs should usually be lowercase letters, numbers, and hyphens.\n' >&2
  exit 1
fi

cat > .firebaserc <<EOF
{
  "projects": {
    "default": "$PROJECT_ID"
  }
}
EOF

printf 'Updated .firebaserc with default project: %s\n' "$PROJECT_ID"
