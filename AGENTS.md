# Repo Agent Guidance

This public repo should be treated as a guarded lonewolf repository.

## GitHub vigilance

- Do not assume GitHub settings from repo files alone. Query the live repo settings before changing branch protection, Actions policy, Pages, or other governance controls.
- Before relaxing any repo protection, widening Actions trust, or making workflow permissions more permissive, stop and get explicit user approval.
- When asked to review or tighten GitHub policy, check at minimum:
  - `actions/permissions`
  - `actions/permissions/workflow`
  - `actions/permissions/fork-pr-contributor-approval`
  - branch protection for `main`
  - repo rulesets
  - Pages state when Pages deploys matter

## Preferred baseline for this repo

- Keep direct owner shipping to `main` acceptable for small, disciplined, low-risk changes.
- Protect `main` from force-pushes and deletion.
- Require approval for all external contributors before fork PR workflows run.
- Restrict GitHub Actions to GitHub-owned actions unless the user explicitly approves a wider allowlist.
- Keep workflow token defaults read-only.
- Keep GitHub Actions unable to approve pull request reviews.

## Documentation

- Record live repo governance state in [REPO_POLICY.md](REPO_POLICY.md) when the baseline changes.
- Keep policy notes public-safe. Do not place private security evidence, tokens, or sensitive admin-only details in tracked docs.
