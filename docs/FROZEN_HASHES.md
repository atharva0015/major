# Frozen file hashes (SHA-256 via `git hash-object`, recorded 2026-10-14)

These files change only with a written reason in `docs/CHANGELOG_FROZEN.md`.
Rule, policy, and Critic logic were verified green (166 passed) before freezing.

| File | SHA-256 (`git hash-object`) |
|---|---|
| `healing/classifier/rules.py` | `979914fd77151753b62072c885ed3a764e5834f6` |
| `healing/critic/checks.py` | `b4967ea84dba703db4bc7b25df3122e9bd497818` |
| `healing/policy/policy.yaml` | `31cdbd25d75113f26628dea55fe2f2f43035be4e` |
| `benchmark/cases.py` | `d387369429e4fa0d18a47cbda7576c3252d16220` |
| `benchmark/api/cases.py` | `0588789ac15f7385d26d3360f2da279ed047b276` |

Notes:
- `benchmark/test_demo.py` and `benchmark/wrong_heals.py` are test/harness
  code, not frozen case data; they are covered by the suite, not this list.
- No `benchmark/heldout/` exists yet; when built, its case files join this
  list with their own entry.

## Re-verification 2026-10-14 (external mini-demo session, before reading code)

`git hash-object` re-run, files NOT opened:
- `healing/classifier/rules.py` → `979914fd77151753b62072c885ed3a764e5834f6` (matches)
- `healing/critic/checks.py` → `b4967ea84dba703db4bc7b25df3122e9bd497818` (matches)
- `healing/policy/policy.yaml` → `31cdbd25d75113f26628dea55fe2f2f43035be4e` (matches)

No frozen file changed; no `CHANGELOG_FROZEN.md` entry needed.
