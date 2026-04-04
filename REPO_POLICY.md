# Repo Policy Baseline

Last verified: April 4, 2026

Repo: [yagaC64/AI_class_public_repo](https://github.com/yagaC64/AI_class_public_repo)

## Intent

This is a public, lonewolf-operated repository. The baseline should make casual outside tinkering harder without adding process for its own sake.

## Lightweight baseline

- Keep direct owner shipping to `main` available for small, low-risk changes.
- Protect `main` from destructive operations.
- Require approval before Actions run for outside contributors.
- Restrict Actions trust to GitHub-owned actions unless explicitly widened.
- Keep workflow token permissions read-only by default.

## Current live GitHub settings

- Visibility: public
- Default branch: `main`

### Actions

- Actions enabled: yes
- Allowed actions: `selected`
- Selected actions policy: GitHub-owned actions allowed, verified creators disallowed, custom allowlist patterns empty
- SHA pinning required: no
- Default workflow permissions: `read`
- GitHub Actions can approve pull request reviews: no
- Fork PR workflow approval policy: `all_external_contributors`

### Branch protection

- `main` branch protection: enabled
- Enforce for admins: yes
- Allow force pushes: no
- Allow deletions: no
- Require pull requests: no
- Require status checks: no
- Require conversation resolution: no
- Lock branch: no

### Rulesets

- Repository rulesets: none

### Merge behavior

- Merge commits allowed: yes
- Rebase merges allowed: yes
- Squash merges allowed: yes
- Delete branch on merge: no

## Why this baseline

- Outside contributors can still open issues and pull requests, but their workflows do not run freely.
- The default branch is protected against the most damaging accidental or hostile operations.
- Owner velocity stays intact because small direct-to-`main` fixes remain possible.

## If stricter controls are needed later

- Require pull requests for `main`
- Require one approving review
- Require named status checks before merge
- Require full-length SHA pinning for all Actions
- Replace branch protection with an explicit ruleset strategy
