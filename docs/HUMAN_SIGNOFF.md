# Human sign-off (all boxes unchecked — only people decide these)

No agent may tick any box. Each item needs a named human, a date, and
either approval or a replacement value with rationale.

## Quality targets (approve or change each of the 12 in docs/TARGETS.md)

- [ ] heal accuracy >= 0.95 (human: ______, date: ______)
- [ ] false-heal rate, overall = 0.0 (human: ______, date: ______)
- [ ] false-heal rate, adversarial = 0.0 on the orchestrator path (raw matcher diagnostic) (human: ______, date: ______)
- [ ] Critic catch rate >= 0.90 (human: ______, date: ______)
- [ ] Critic false-reject rate <= 0.05 (human: ______, date: ______)
- [ ] classification accuracy >= 0.95 (human: ______, date: ______)
- [ ] genuine regressions passed to heal engine = 0 (human: ______, date: ______)
- [ ] auto-healed contract changes = 0 (human: ______, date: ______)
- [ ] cost per heal <= 2.0 units (human: ______, date: ______)
- [ ] pipeline latency <= 100 ms (browser latency diagnostic) (human: ______, date: ______)
- [ ] alert completeness = 1.0 (human: ______, date: ______)
- [ ] heal survival rate TBD (human: ______, date: ______)

## Legal and compliance

- [ ] Legal review of docs/COMPLIANCE.md (human: ______, date: ______)
- [ ] LICENSE choice from docs/LICENSE_DECISION.md (human: ______, date: ______)
- [ ] Vendor register approval, DPAs, owners (human: ______, date: ______)

## Release

- [ ] Next tag may be cut (human: ______, date: ______)
  - Blockers a tagger must confirm resolved: live adversarial containment
    re-verified, held-out set built and measured, survival gate activated
    or formally deferred, CI green on 3.12 observed.
