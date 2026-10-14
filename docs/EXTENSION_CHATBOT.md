# EXTENSION_CHATBOT -- deferred, with reasons and revisit criteria

No chatbot code exists or was written for this document (`healing/chatbot/`
does not exist; no MCP server, tools, or red-team suite). This records the
deferral so the option stays visible and reviewable. Status: **DEFERRED**.

## Why deferred (not dropped)

- **MVP not blocked.** Every capability the chatbot would offer (record
  lookup, diff proposal, sandbox run, branch commit, PR comment,
  quarantine, heal rejection) already exists as deterministic code paths
  exercised by tests and benches. A conversational layer adds interface
  risk without new healing power.
- **Review workload evidence.** The current backlog is human sign-offs, not
  information access: TARGETS.md targets unapproved, GATE_REVIEW checklist
  unchecked, COMPLIANCE vendor register blank, LICENSE undecided. A
  chatbot answers questions; the bottleneck is decisions. Adding it now
  would widen the review surface while the existing queue is unaudited.

## Red-team plan (for the revisit, not executed)

When revisited, the suite must cover, at minimum: prompt injection
through page text, logs, and PR comments (treated as quoted data, never
instructions); scope-escape attempts (reads/writes outside heal branches);
requests to weaken or remove assertions (require second reviewer);
attempts to push to `main` or protected branches (must refuse + audit);
identity/role enforcement and rate limits on every tool; confirmation
tokens bound to exact diffs for `commit_to_heal_branch`. All attacks must
be blocked and audited, mirroring the fail-closed bar the rest of the
system meets.

## Revisit criteria (all must hold)

1. The TARGETS.md sign-off checklist is fully approved by a human.
2. Evidence that reviewers spend material time *retrieving* heal context
   (as opposed to deciding) — e.g., measured alert-acknowledgement latency
   dominated by lookup, not judgment.
3. The red-team suite above is written first and green against a stub
   server before any model is connected.
4. External model calls go through `healing/security/masking.py` with
   self-hosted endpoint config, same as the vision/LLM extension.

## Recommendation: DEFERRED

Revisit only when all four criteria hold. Do not build a chatbot to
demonstrate capability; build it when reviewer toil evidence demands it.
