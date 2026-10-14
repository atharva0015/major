"""Tests for live-bench helpers: pure logic, recorded fixtures, no Docker."""

import pytest
import yaml

from scripts.bench_healenium_live import adversarial_block, naive_id_from_locator
from scripts.live_healenium_check import extract_score, find_healing_entry


def test_naive_id_parsing() -> None:
    assert naive_id_from_locator(' id="login-submit"') == "login-submit"
    with pytest.raises(ValueError):
        naive_id_from_locator("//button[@id='x']")


def test_find_entry_matches_locator_substring() -> None:
    payload = {
        "data": [
            {"locator": "id=other", "score": 0.1},
            {"locator": "id=login-submit", "score": 0.87},
        ]
    }
    entry = find_healing_entry(payload, "login-submit")
    assert entry is not None and entry["score"] == 0.87
    assert find_healing_entry(payload, "nope") is None
    assert find_healing_entry({"data": "garbage"}, "x") is None
    assert find_healing_entry({"items": [{"score": 0.5}]}, "x") is None


def test_extract_score_accepts_only_unit_floats() -> None:
    assert extract_score({"score": 0.87}) == 0.87
    assert extract_score({"score": "0.87"}) == 0.87  # live backend string-encodes
    assert extract_score({}) is None
    assert extract_score({"score": 87}) is None  # percent-scale is not a score
    assert extract_score({"score": True}) is None
    assert extract_score({"score": "high"}) is None
    assert extract_score({"healingScore": 1}) is None  # never observed live: rejected


def test_adversarial_block_counts() -> None:
    from healing.quality.metrics import RunResult

    results = [
        RunResult("a:/x", False, True, False, False),
        RunResult("b:/x", False, False, False, True),
    ]
    text = adversarial_block(results)
    assert "adversarial false heals: 1" in text


def test_best_score_uses_verbatim_live_shape() -> None:
    """Recorded live entry: score is a string, key set is fixed."""
    from healing.matching.healenium_adapter import best_score_for_locator

    payload = {
        "data": [
            {
                "declaringClass": '[id="login-submit"]',
                "failedLocatorType": "By.cssSelector",
                "failedLocatorValue": '[id="login-submit"]',
                "healedLocatorType": "By.cssSelector",
                "healedLocatorValue": "button#login-submit-v2",
                "healingResultId": 1,
                "score": "0.97",
                "successHealing": True,
            }
        ]
    }
    assert best_score_for_locator(payload, "login-submit") == 0.97
    assert best_score_for_locator(payload, "nope") is None
    assert best_score_for_locator({"data": "garbage"}, "x") is None
    assert best_score_for_locator({"items": [{"score": 0.5}]}, "x") is None


def test_compose_uses_grid_not_selenoid() -> None:
    """Selenoid cannot spawn browsers on Docker API >= 1.40; Grid is required."""
    with open("infra/docker-compose.yml", encoding="utf-8") as f:
        compose = yaml.safe_load(f)
    images = [svc.get("image", "") for svc in compose["services"].values()]
    assert not any("aerokube" in img for img in images)
    assert any(img.startswith("selenium/hub") for img in images)
    assert any(img.startswith("selenium/node-chromium") for img in images)
    proxy_env = compose["services"]["hlm-proxy"]["environment"]
    assert "SELENIUM_SERVER_URL=http://selenium-hub:4444/wd/hub" in proxy_env
