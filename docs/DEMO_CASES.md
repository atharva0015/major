# Demo-cases report (SIMULATED — Docker daemon down, no live runs possible)

External mini-demo: Submit-order step under 24 drift scenarios (12 original
+ 12 harder blind cases), built as self-contained fixtures in
`benchmark/demo_cases/` (frozen pipeline and demo_app untouched).
Expectations were fixed in `cases.yaml` BEFORE any run, including the 12
new ones. Per-set tables below; counts separated for pipeline vs sim-alone.

- cases: 24 (expected HEAL: 11, expected ESCALATE: 13)
- pipeline false heals: 0 (SIMULATED)
- pipeline wrong escalations: 0 (SIMULATED)
- sim-alone false heals: 0 (SIMULATED)
- sim-alone wrong escalations: 0 (SIMULATED)
- failures: none. Nothing was fixed (nothing failed).

## Per-case results, original set (all SIMULATED)

| case | expected | pipeline | ok | sim-alone | sim ok | critic | decision |
|---|---|---|---|---|---|---|---|
| renamed_id | HEAL | submit-order | True | submit-order | True | pass:all-layers | heal_unverified |
| reskinned | HEAL | submit-order | True | submit-order | True | pass:all-layers | heal_unverified |
| moved | HEAL | submit-order | True | submit-order | True | pass:all-layers | heal_unverified |
| label_reworded | HEAL | submit-order | True | submit-order | True | pass:all-layers | heal_unverified |
| lookalike_trap | ESCALATE | ESCALATE | True | ESCALATE | True | n/a (escalated) | fail_escalate |
| duplicates | ESCALATE | ESCALATE | True | ESCALATE | True | n/a (escalated) | fail_escalate |
| button_removed | ESCALATE | ESCALATE | True | ESCALATE | True | n/a (escalated) | fail_escalate |
| save_draft_vs_save_order | ESCALATE | ESCALATE | True | ESCALATE | True | n/a (escalated) | fail_escalate |
| delete_account_vs_delete_draft | ESCALATE | ESCALATE | True | ESCALATE | True | n/a (escalated) | fail_escalate |
| disabled_submit | ESCALATE | ESCALATE | True | ESCALATE | True | n/a (escalated) | fail_escalate |
| renamed_id_and_text | HEAL | submit-order | True | submit-order | True | pass:all-layers | heal_unverified |
| single_char_typo | HEAL | submit-order | True | submit-order | True | pass:all-layers | heal_unverified |

## Per-case results, harder blind set (all SIMULATED)

| case | expected | pipeline | ok | sim-alone | sim ok | critic | decision |
|---|---|---|---|---|---|---|---|
| hidden_submit | ESCALATE | ESCALATE | True | ESCALATE | True | n/a (escalated) | fail_escalate |
| iframe_submit | ESCALATE | ESCALATE | True | ESCALATE | True | n/a (escalated) | fail_escalate |
| translated_label | HEAL | submit-order | True | submit-order | True | pass:all-layers | heal_unverified |
| shortened_label | HEAL | submit-order | True | submit-order | True | pass:all-layers | heal_unverified |
| near_identical_pair | ESCALATE | ESCALATE | True | ESCALATE | True | n/a (escalated) | fail_escalate |
| link_replaces_button | HEAL | submit-order | True | submit-order | True | pass:all-layers | heal_unverified |
| reordered_steps | ESCALATE | ESCALATE | True | ESCALATE | True | n/a (escalated) | fail_escalate |
| cookie_covered | ESCALATE | ESCALATE | True | ESCALATE | True | n/a (escalated) | fail_escalate |
| redesign_removed | ESCALATE | ESCALATE | True | ESCALATE | True | n/a (escalated) | fail_escalate |
| ab_continue_variant | HEAL | submit-order | True | submit-order | True | pass:all-layers | heal_unverified |
| duplicate_ids | ESCALATE | ESCALATE | True | ESCALATE | True | n/a (escalated) | fail_escalate |
| action_changed | ESCALATE | ESCALATE | True | ESCALATE | True | n/a (escalated) | fail_escalate |

## Honest caveats

- The sim-alone comparison is weak by construction: with custom
  `demo:*` drift names the simulator falls through to "heal iff the
  stable testid survives", so it agrees with expectations wherever the
  testid is present/absent. It cannot distinguish these scenarios.
- `duplicates` escalated via Critic rejection on attempt 1
  (`critic_fail`), not via ambiguity detection — probed separately and
  recorded here.
- Harder set: all 12 matched, including `iframe_submit`,
  `cookie_covered`, `near_identical_pair`, and `action_changed`, which
  escalate via attempt-1 `critic_fail` (no correct element ⇒ intent can
  never pass) followed by reweighted `ambiguous_candidates`. The
  escalations are structurally fail-closed, not lucky.
- `label_reworded` healed as `heal_unverified`, matching the
  needs-review expectation in outcome (escalation avoided) though the
  record does not carry an explicit review flag — noted, not tuned.
- No live runs: Docker daemon unreachable from this environment.
