# Baseline run results (tag `baseline-v0`, branch `chore/baseline`)

Full logs: `reports/run_logs/<command>.txt` (command name with dots/slashes
replaced by dashes/dots as shown). No failures were fixed in this session.

Environment: Windows, Python 3.10.9, no `make` binary. All `make ...`
invocations fail with CommandNotFound; each log therefore also contains the
exact Makefile body run directly, labeled EQUIVALENT. `pip install -e .` was
not attempted (pyproject requires Python >=3.12); pytest runs from the repo
root. Selenium is not installed; its one test skips by design.

| Command | Result | Key numbers |
|---|---|---|
| `make lint` | FAILED (no make) / equivalent PASS exit 0 | ruff clean, 121 files formatted, mypy 50 files clean |
| `make test` | FAILED (no make) / equivalent PASS exit 0 | 146 passed |
| `make bench` | FAILED (no make) / equivalent PASS exit 0 | baseline acc 0.000 esc 1.000; verify catch 0.667, false-reject 0.000, false-heal 0.000, attempt-1 15/15 |
| `make bench-healenium` | FAILED (no make) / equivalent PASS exit 0 | sim acc 1.000, FHR 0.286, adversarial 6/9 healed (sim, live False) |
| `make bench-shadow` | FAILED (no make) / equivalent PASS exit 0 | 0 PRs opened, 0 escaped defects |
| `make bench-api` | FAILED (no make) / equivalent PASS exit 0 | 7 cases, 0 auto-healed contracts, FHR 0.000 |
| `make bench-golden` | FAILED (no make) / equivalent PASS exit 0 | mismatches none, acc 1.000, FHR 0.000, PASS |
| `make bench-vision` | FAILED (no make) / equivalent PASS exit 0 | top-1 15/15, ambiguous 15/15, wins 1:15/2-4:0, verdict DROP |
| `python -m scripts.bench_decision` | PASS exit 0 | accuracy 1.000, 0 genuine passed to heal engine |
| `python -m scripts.bench_verify` | PASS exit 0 | catch 0.667, false-reject 0.000, false-heal 0.000 |
| `python -m scripts.sbom` | PASS exit 0 | 216 components |
| `python -m scripts.retention` | PASS exit 0 | dry_run true, 0 deletions |

First error (all eight `make` commands, identical root cause):

```text
The term 'make' is not recognized as the name of a cmdlet, function, script
file, or operable program.
```

NOT RUN: nothing. Every command either ran directly or ran via its exact
Makefile body. Docker was not needed (no `docker up/down` executed;
live-backend and live-Postgres paths remain unverified by design).
