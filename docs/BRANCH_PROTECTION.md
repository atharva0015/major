# Branch protection for heal PRs (human setup, repo Settings)

Required on `main`:

- Require pull request before merging (no direct pushes; bot included).
- Required approvals: 1+, and **dismiss stale reviews**; the `policy-check`
  job rejects PRs whose only approval is the triggering identity.
- Required status checks: `unit-tests`, `healed-on-staging`, `stability`,
  `negative-check`, `secret-scan`, `policy-check`.
- Require signed commits; require linear history if desired.
- No force-push, no deletion; include administrators.
- CODEOWNERS review required for `healing/**` (`docs/CODEOWNERS` pattern).

Manual steps for a human: create the GitHub App, install it on the repo,
set `GITHUB_APP_ID` / `GITHUB_PRIVATE_KEY_PATH` / `GITHUB_INSTALLATION_ID` /
`GITHUB_REPO` secrets/vars, enable the settings above, add CODEOWNERS.
