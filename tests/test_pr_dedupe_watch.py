"""Tests for PR body completeness, dedupe, and post-merge watch."""

from healing.gitops.app import PullRequest
from healing.gitops.dedupe import group_by_locator, plan_prs
from healing.gitops.pr_template import body_complete, build_pr_body
from healing.gitops.watch import on_failure, should_watch


def body() -> str:
    return build_pr_body(
        "s", "d", 0.9, "pass", "rec", "hash", "b.png", "a.png", "c.png", "sandbox://1", "revert me"
    )


def test_pr_body_has_every_required_section() -> None:
    ok, missing = body_complete(body())
    assert ok and missing == []
    assert "needs-human" in body()


def test_pr_body_reports_missing_sections() -> None:
    ok, missing = body_complete("empty")
    assert not ok and len(missing) == 8


def test_dedupe_single_pr_for_shared_locator() -> None:
    failures = [{"test": f"t{i}", "locator": "login-submit"} for i in range(3)]
    failures.append({"test": "t9", "locator": "other"})
    plans = plan_prs(group_by_locator(failures))
    assert len(plans) == 2
    shared = next(p for p in plans if p["locator"] == "login-submit")
    assert sorted(shared["tests"]) == ["t0", "t1", "t2"]  # type: ignore[typeddict-item]


def test_watch_window_and_revert_alert() -> None:
    assert should_watch(1000.0, 24, now=1000.0 + 60) is True
    assert should_watch(1000.0, 24, now=1000.0 + 25 * 3600) is False

    class FakeClient:
        def __init__(self) -> None:
            self.prs = [PullRequest(1, "heal/a-1", "main", "t", "b")]

        def open_revert_pr(self, pr, reason):  # type: ignore[no-untyped-def]
            rp = PullRequest(2, "revert/heal-a-1", pr.base, "Revert t", reason, ["revert"])
            self.prs.append(rp)
            return rp

    seen: list[str] = []
    rec = on_failure(
        "t", PullRequest(1, "heal/a-1", "main", "t", "b"), "flaky", FakeClient(), seen.append
    )  # type: ignore[arg-type]
    assert rec == {"test": "t", "revert_pr": 2, "reason": "flaky"}
    assert len(seen) == 1
