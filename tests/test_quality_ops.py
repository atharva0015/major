"""Tests for version registry, replay, observability, retention, SBOM."""

import json

from healing.alerts.model import acknowledge, build_alert
from healing.quality.observability import (
    observe_ack,
    observe_escalation,
    observe_heal,
    traced,
)
from healing.quality.registry import current_versions, record_versions, replay_heal
from healing.security.retention import plan_deletions, run
from healing.xai.records import make_record


def test_registry_pins_versions() -> None:
    pin = current_versions()
    assert (pin.model, pin.policy, pin.config) == ("rules-0.1.0", "policy-0.1.0", "config-0.1.0")
    assert record_versions(pin) == pin


def test_replay_reproduces_heal() -> None:
    rec = make_record(
        heal_id="heal-r1", test="t", classification="locator_drift", selected="login-submit"
    )
    out = replay_heal(rec, "html login-submit", ["login-submit", "login-cancel"])
    assert out["matches_record"] is True
    assert out["reproduced_selected"] == "login-submit"


def test_observability_calls_record_metrics() -> None:
    with traced("test.span"):
        observe_heal(1, True, 0.05, 1.0)
        observe_escalation("locator_drift")
        observe_ack(12.0)
    from prometheus_client import REGISTRY

    names = {c.name for c in REGISTRY.collect() for s in c.samples}
    assert any("heal_latency" in n or "heal_success" in n for n in names)


def test_acknowledge_marks_and_observes() -> None:
    a = build_alert(
        "t",
        "locator_drift",
        [],
        {"before": "b", "after": "a", "candidate": "c"},
        "next",
        "replay://1",
    )
    acknowledge(a, at=a.ack_deadline_s - 3500.0)
    assert a.acknowledged is True


def test_retention_dry_run_by_default(tmp_path) -> None:
    old = tmp_path / "audit.log"
    old.write_text("x\n")
    import os
    import time

    ancient = time.time() - 400 * 86400.0
    os.utime(old, (ancient, ancient))
    plan = plan_deletions(str(tmp_path))
    assert any(p["path"].endswith("audit.log") for p in plan)
    out = run(str(tmp_path))  # dry-run default
    assert out["dry_run"] is True and old.exists()
    out = run(str(tmp_path), apply=True)
    assert out["dry_run"] is False and not old.exists()


def test_dashboard_json_valid() -> None:
    dash = json.load(open("infra/grafana-dashboard.json"))
    titles = [p["title"] for p in dash["panels"]]
    assert len(dash["panels"]) == 5
    for want in ("latency", "cost", "success by attempt", "Escalations", "acknowledgement"):
        assert any(want.lower() in t.lower() for t in titles)


def test_sbom_builds_locally(tmp_path, monkeypatch) -> None:
    from scripts import sbom as sbom_mod

    monkeypatch.setattr(sbom_mod, "OUT", str(tmp_path / "sbom.json"))
    sbom_mod.main()
    data = json.loads(open(str(tmp_path / "sbom.json")).read())
    assert data["components"]
    assert any(c["name"] == "pytest" for c in data["components"])
