# Frozen file hashes (`git hash-object`, SHA-1 blob IDs, recorded 2026-10-14)

These files change only with a written reason in `docs/CHANGELOG_FROZEN.md`.
Rule, policy, and Critic logic were verified green (166 passed) before freezing.

The values below are Git's SHA-1 blob IDs (40 hex characters). Earlier
revisions of this file called them SHA-256; that label was wrong.

| File | SHA-1 blob ID (`git hash-object`) |
|---|---|
| `healing/classifier/rules.py` | `979914fd77151753b62072c885ed3a764e5834f6` |
| `healing/critic/checks.py` | `b4967ea84dba703db4bc7b25df3122e9bd497818` |
| `healing/policy/policy.yaml` | `31cdbd25d75113f26628dea55fe2f2f43035be4e` |
| `benchmark/cases.py` | `d387369429e4fa0d18a47cbda7576c3252d16220` |
| `benchmark/api/cases.py` | `0588789ac15f7385d26d3360f2da279ed047b276` |
| `benchmark/heldout/ui_cases.py` | `7200caae7a5621ac34f5a09391e47ba12c7972a7` |
| `benchmark/heldout/api_cases.py` | `0cc0349962b0473eb8df9b5a600bc7da0fb378f7` |

Notes:
- `benchmark/test_demo.py` and `benchmark/wrong_heals.py` are test/harness
  code, not frozen case data; they are covered by the suite, not this list.
- `benchmark/heldout/ui_cases.py` and `api_cases.py` were added on
  2026-10-14 and are frozen here as of 2026-11-04. They are the held-out
  inputs; their expectations must not be tuned after seeing results.

`tests/test_frozen_hashes.py` parses this table and recomputes every listed
hash. A missing file, a missing required entry, or a mismatch fails the suite.
This replaces the manual `git hash-object` check.

## Re-verification 2026-10-14 (external mini-demo session, before reading code)

`git hash-object` re-run, files NOT opened:
- `healing/classifier/rules.py` → `979914fd77151753b62072c885ed3a764e5834f6` (matches)
- `healing/critic/checks.py` → `b4967ea84dba703db4bc7b25df3122e9bd497818` (matches)
- `healing/policy/policy.yaml` → `31cdbd25d75113f26628dea55fe2f2f43035be4e` (matches)

No frozen file changed; no `CHANGELOG_FROZEN.md` entry needed.

## Re-verification 2026-11-04

`git hash-object` re-run for all seven entries above; all hashes **match**
(no differences). Full output:
`reports/evidence/2026-11-04/frozen-hashes.txt`.

One record gap remains, flagged for a human:

- The freeze rationale says "166 passed"; the current suite is **201
  passed** (2026-11-06).

No `CHANGELOG_FROZEN.md` entry was needed: no previously frozen file changed.
Adding the two held-out files records their initial freeze, not a change to
rule, policy, or Critic logic.
