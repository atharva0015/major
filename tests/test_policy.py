"""Tests for policy engine: ambiguity rule + every decision branch."""

from healing.policy.engine import PolicyConfig, decide, load_config


def cfg(**kw: object) -> PolicyConfig:  # type: ignore[no-untyped-def]
    base = load_config().__dict__
    base.update(kw)
    return PolicyConfig(**{k: v for k, v in base.items() if k != "raw"})


def test_high_confidence_critic_pass_heals_pr() -> None:
    d = decide("locator_drift", 0.9, 0.5, True, cfg())
    assert d.action == "heal_pr"


def test_medium_confidence_heals_unverified() -> None:
    d = decide("locator_drift", 0.6, 0.5, None, cfg())
    assert d.action == "heal_unverified"


def test_high_unverified_stub_is_unverified() -> None:
    d = decide("locator_drift", 0.95, 0.5, None, cfg())
    assert d.action == "heal_unverified"


def test_low_confidence_escalates() -> None:
    d = decide("locator_drift", 0.2, 0.5, None, cfg())
    assert (d.action, d.reason) == ("fail_escalate", "low_confidence")


def test_critic_fail_escalates() -> None:
    d = decide("locator_drift", 0.95, 0.5, False, cfg())
    assert (d.action, d.reason) == ("fail_escalate", "critic_fail")


def test_ambiguity_margin_escalates() -> None:
    c = cfg()
    d = decide("locator_drift", 0.95, c.ambiguity_margin / 2, True, c)
    assert d.ambiguous and d.action == "fail_escalate"


def test_blocked_class_never_heals() -> None:
    for blocked in ("genuine_regression", "environment_issue", "contract_change"):
        d = decide(blocked, 0.99, 1.0, True, cfg())
        assert d.action == "fail_escalate"


def test_kill_switch_blocks_all() -> None:
    d = decide("locator_drift", 0.99, 1.0, True, cfg(kill_switch=True))
    assert (d.action, d.reason) == ("fail_escalate", "kill_switch_engaged")


def test_l1_downgrades_to_propose() -> None:
    d = decide("locator_drift", 0.9, 0.5, True, cfg(autonomy_level="L1"))
    assert d.action == "propose"
