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
        f'- metric: {m}\n  op: "{op}"\n  value: {v}\n  source: {s}' for m, op, v, s in rows
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
            ("critic_catch_rate", ">=", 0.9, v),
            ("cost_per_heal", "<=", 2.0, h),
        ],
    )
    monkeypatch.setattr(cg, "TARGETS_MD", t)
    monkeypatch.setattr(cg, "check_alerts", lambda: ("PASS", "stubbed"))
    cg.main()  # exit 0: no exception
    out = capsys.readouterr().out
    assert "PASS critic_catch_rate" in out and "result: PASS" in out

    v2 = write(
        tmp_path / "v2.json", {"catch_rate": 0.5, "false_heal_rate": 0.0, "false_reject_rate": 0.0}
    )
    t2 = targets(tmp_path, [("critic_catch_rate", ">=", 0.9, v2)])
    monkeypatch.setattr(cg, "TARGETS_MD", t2)
    with pytest.raises(SystemExit) as exc:
        cg.main()
    assert exc.value.code == 1
    assert "FAIL critic_catch_rate" in capsys.readouterr().out


def test_metric_value_reads_nested_keys(tmp_path) -> None:
    p = write(tmp_path / "h.json", {"metrics": {"cost_per_heal": 1.0}})
    assert cg.metric_value("cost_per_heal", p) == 1.0
