"""Tests for the gate checker: pass, fail, and fail-closed paths."""

import json

import pytest

from scripts import check_gates as cg


def write(path, payload) -> str:  # type: ignore[no-untyped-def]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    return str(path)


def targets(tmp_path, rows) -> str:  # type: ignore[no-untyped-def]
    p = tmp_path / "TARGETS.md"
    block = "\n".join(
        f'- metric: {m}\n  op: "{op}"\n  value: {v}\n  source: {s}\n  provenance: {prov}'
        for m, op, v, s, prov in rows
    )
    p.write_text("# T\n\n```yaml targets\n" + block + "\n```\n")
    return str(p)


def test_load_targets_rejects_missing_block(tmp_path) -> None:
    p = tmp_path / "T.md"
    p.write_text("# no block\n")
    with pytest.raises(ValueError):
        cg.load_targets(str(p))


def test_adversarial_rate_from_results(tmp_path) -> None:
    p = write(
        tmp_path / "h.json",
        {
            "results": [
                {"should_heal": False, "healed": True, "correct": False},
                {"should_heal": False, "healed": False},
                {"should_heal": True, "healed": True, "correct": True},
            ]
        },
    )
    assert cg.adversarial_fhr(p) == 1.0


def test_adversarial_rate_zero_when_nothing_healed(tmp_path) -> None:
    p = write(
        tmp_path / "h.json",
        {
            "results": [
                {"should_heal": False, "healed": False},
            ]
        },
    )
    assert cg.adversarial_fhr(p) == 0.0


def test_missing_report_is_fail_closed(tmp_path) -> None:
    with pytest.raises(OSError):
        cg.metric_value("heal_accuracy", str(tmp_path / "nope.json"))


def test_main_pass_and_fail(tmp_path, monkeypatch, capsys) -> None:
    v = write(
        tmp_path / "v.json", {"catch_rate": 0.95, "false_heal_rate": 0.0, "false_reject_rate": 0.0}
    )
    h = write(tmp_path / "h.json", {"metrics": {"cost_per_heal": 1.0}, "results": []})
    t = targets(
        tmp_path,
        [
            ("critic_catch_rate", ">=", 0.9, v, "sim"),
            ("cost_per_heal", "<=", 2.0, h, "sim"),
        ],
    )
    monkeypatch.setattr(cg, "TARGETS_MD", t)
    monkeypatch.setattr(cg, "check_alerts", lambda: ("PASS", "stubbed"))
    cg.main()  # exit 0: no exception
    out = capsys.readouterr().out
    assert "PASS critic_catch_rate" in out and "result: PASS" in out
    assert "MEASURED PASS 3 / FAIL 0 / UNVERIFIED 1" in out

    v2 = write(
        tmp_path / "v2.json", {"catch_rate": 0.5, "false_heal_rate": 0.0, "false_reject_rate": 0.0}
    )
    t2 = targets(tmp_path, [("critic_catch_rate", ">=", 0.9, v2, "sim")])
    monkeypatch.setattr(cg, "TARGETS_MD", t2)
    with pytest.raises(SystemExit) as exc:
        cg.main()
    assert exc.value.code == 1
    assert "FAIL critic_catch_rate" in capsys.readouterr().out


def test_metric_value_reads_nested_keys(tmp_path) -> None:
    p = write(tmp_path / "h.json", {"metrics": {"cost_per_heal": 1.0}})
    assert cg.metric_value("cost_per_heal", p) == 1.0


def test_live_source_mapping() -> None:
    assert (
        cg.live_source_for("benchmark/reports/healenium.json")
        == "benchmark/reports/healenium_live.json"
    )
    assert (
        cg.live_source_for("benchmark/reports/golden.json") == "benchmark/reports/golden_live.json"
    )


def test_live_gate_uses_live_file(tmp_path, monkeypatch, capsys) -> None:
    live = write(
        tmp_path / "h_live.json",
        {
            "metrics": {"heal_accuracy": 1.0},
            "vias": [{"should_heal": False, "healed": False}],
        },
    )
    sim = write(
        tmp_path / "h.json",
        {
            "metrics": {},
            "results": [
                {"should_heal": False, "healed": True, "correct": False},
            ],
        },
    )
    assert cg.live_source_for(sim) == live  # checker resolves sim->live this way
    t = targets(
        tmp_path,
        [
            ("false_heal_rate_adversarial", "==", 0.0, sim, "live"),
            ("heal_accuracy", ">=", 0.95, tmp_path / "g.json", "live"),
        ],
    )
    write(tmp_path / "g_live.json", {"metrics": {"heal_accuracy": 1.0}})
    write(tmp_path / "g.json", {"accuracy": 0.0})
    monkeypatch.setattr(cg, "TARGETS_MD", t)
    monkeypatch.setattr(cg, "check_alerts", lambda: ("PASS", "stubbed"))
    cg.main()
    out = capsys.readouterr().out
    assert "PASS false_heal_rate_adversarial [live]" in out
    assert "PASS heal_accuracy [live]" in out


def test_live_gate_missing_file_is_unverified_not_pass(tmp_path, monkeypatch, capsys) -> None:
    sim = write(tmp_path / "h.json", {"metrics": {"cost_per_heal": 99.0}, "results": []})
    t = targets(tmp_path, [("cost_per_heal", "<=", 2.0, sim, "live")])
    monkeypatch.setattr(cg, "TARGETS_MD", t)
    monkeypatch.setattr(cg, "check_alerts", lambda: ("PASS", "stubbed"))
    cg.main()  # exit 0 despite sim value 99.0 violating the bar
    out = capsys.readouterr().out
    assert "UNVERIFIED cost_per_heal [live]" in out
    assert "sim data must not stand in" in out
    assert "MEASURED PASS 1 / FAIL 0 / UNVERIFIED 2" in out


def test_evaluate_returns_structured_rows(tmp_path, monkeypatch) -> None:
    v = write(
        tmp_path / "v.json", {"catch_rate": 0.95, "false_heal_rate": 0.0, "false_reject_rate": 0.0}
    )
    t = targets(tmp_path, [("critic_catch_rate", ">=", 0.9, v, "sim")])
    monkeypatch.setattr(cg, "TARGETS_MD", t)
    monkeypatch.setattr(cg, "check_alerts", lambda: ("PASS", "stubbed"))

    rows = cg.evaluate()
    assert rows[0]["metric"] == "critic_catch_rate"
    assert rows[0]["status"] == "PASS"
    assert rows[0]["actual"] == 0.95
    assert rows[1]["metric"] == "alert_completeness"
    assert rows[1]["status"] == "PASS"
    assert rows[-1]["metric"] == "heal_survival_rate"
    assert rows[-1]["status"] == "UNVERIFIED"
