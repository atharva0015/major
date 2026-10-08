"""Tests for layered Critic: each layer catches its fault class."""

from healing.critic.checks import (
    DisabledJudge,
    apply_judge,
    run_checks,
)

HTML = (
    "<html><body><main>"
    '<button id="login-submit" data-testid="login-submit" class="btn">Sign In</button>'
    '<button id="login-cancel" data-testid="login-cancel" class="btn">Cancel</button>'
    "</main></body></html>"
)
BASE = HTML
KEYS = ["login-submit", "login-cancel"]


def test_correct_heal_passes_all_layers() -> None:
    v = run_checks(HTML, "login-submit", "login-submit", BASE, KEYS, [], ["demo"], "submit")
    assert v.passed is True and v.failed_layer is None


def test_deterministic_catches_duplicate() -> None:
    dup = HTML.replace("</main>", '<button data-testid="login-submit">x</button></main>')
    v = run_checks(dup, "login-submit", "login-submit", BASE, KEYS, [], ["demo"], "submit")
    assert v.passed is False and v.failed_layer == "deterministic"


def test_deterministic_catches_removed() -> None:
    gone = HTML.replace('data-testid="login-submit"', 'data-testid="gone"')
    v = run_checks(gone, "login-submit", "login-submit", BASE, KEYS, [], ["demo"], "submit")
    assert v.passed is False and v.failed_layer == "deterministic"


def test_state_catches_missing_keys() -> None:
    v = run_checks(
        HTML, "login-submit", "login-submit", BASE, ["login-submit", "nope"], [], ["demo"], "submit"
    )
    assert v.passed is False and v.failed_layer == "state"


def test_network_catches_new_host() -> None:
    v = run_checks(
        HTML,
        "login-submit",
        "login-submit",
        BASE,
        KEYS,
        ["https://evil.example/x"],
        ["demo"],
        "submit",
    )
    assert v.passed is False and v.failed_layer == "network"


def test_intent_catches_wrong_role() -> None:
    v = run_checks(HTML, "login-cancel", "login-submit", BASE, KEYS, [], ["demo"], "submit")
    assert v.passed is False and v.failed_layer == "intent"


def test_disabled_judge_changes_nothing() -> None:
    v = run_checks(HTML, "login-submit", "login-submit", BASE, KEYS, [], ["demo"], "submit")
    assert apply_judge(v, DisabledJudge()).passed is True


def test_judge_cannot_override_failure() -> None:
    class Eager:
        enabled = True

        def review(self, html: str, chosen: str) -> float:
            return 1.0

    v = run_checks(HTML, "login-cancel", "login-submit", BASE, KEYS, [], ["demo"], "submit")
    assert apply_judge(v, Eager()).passed is False  # type: ignore[arg-type]


def test_judge_can_only_lower_confidence() -> None:
    class Harsh:
        enabled = True

        def review(self, html: str, chosen: str) -> float:
            return 0.5

    v = run_checks(HTML, "login-submit", "login-submit", BASE, KEYS, [], ["demo"], "submit")
    out = apply_judge(v, Harsh())  # type: ignore[arg-type]
    assert out.passed is True and out.confidence_multiplier == 0.5
