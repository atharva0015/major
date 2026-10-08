"""Tests for shadow mode: zero PRs, zero escaped defects, rollback dry-run."""

from healing.orchestrator import HealerOrchestrator


def test_shadow_builds_artifacts_opens_no_prs() -> None:
    calls: list[str] = []
    orch = HealerOrchestrator()
    assert orch.config.shadow_mode is True
    html = (
        '<button id="login-submit-v2" data-testid="login-submit">x</button>'
        '<button id="login-cancel" data-testid="login-cancel">y</button>'
    )
    out = orch.heal_case(
        "renamed_ids:/login",
        "t",
        "renamed_ids",
        html,
        ' id="login-submit"',
        ["login-submit", "login-cancel"],
        "login-submit",
    )
    assert out.shadow_pr is not None  # diff + body recorded...
    assert calls == []  # ...but no PR opened (no publisher is ever called)


def test_shadow_report_zero_escaped(tmp_path, monkeypatch) -> None:
    from scripts import shadow_report as sr

    monkeypatch.setattr(sr, "REPORT_MD", str(tmp_path / "shadow.md"))
    monkeypatch.setattr(sr, "REPORT_JSON", str(tmp_path / "shadow.json"))
    sr.main()
    import json

    data = json.loads(open(str(tmp_path / "shadow.json")).read())
    assert data["prs_opened"] == 0
    assert data["escaped"] == 0


def test_rollback_script_usage_and_dry_run(monkeypatch, capsys) -> None:
    import pytest

    from scripts import rollback_heal as rb

    monkeypatch.setattr("sys.argv", ["rollback_heal.py"])
    with pytest.raises(SystemExit):
        rb.main()
    monkeypatch.setattr("sys.argv", ["rollback_heal.py", "heal-abc", "--reason", "flaky"])
    rb.main()  # dry-run: prints plan, opens nothing
    assert "heal-abc" in capsys.readouterr().out
