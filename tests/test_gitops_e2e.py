"""End-to-end (fixtures): fail -> heal -> Critic -> diff -> PR body -> negative check."""

import os
import subprocess

from healing.critic.checks import run_checks
from healing.gitops.app import LocalBareRepoClient, reviews_valid
from healing.gitops.ast_edit import edit_locator
from healing.gitops.pr_template import body_complete, build_pr_body
from healing.orchestrator import HealerOrchestrator

BASE_HTML = (
    "<html><body><main>"
    '<button id="login-submit" data-testid="login-submit" class="btn">Sign In</button>'
    "</main></body></html>"
)
DRIFTED_HTML = BASE_HTML.replace(' id="login-submit"', ' id="login-submit-v2"')
REMOVED_HTML = "<html><body><main></main></body></html>"

SOURCE = open(os.path.join("healing", "gitops", "fixtures", "sample_test.py")).read()


def repo(tmp_path):  # type: ignore[no-untyped-def]
    remote, work = tmp_path / "r.git", tmp_path / "w"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "clone", str(remote), str(work)], check=True, capture_output=True)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=work, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=work, check=True)
    (work / "sample_test.py").write_text(SOURCE)
    subprocess.run(["git", "add", "."], cwd=work, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=work, check=True, capture_output=True)
    subprocess.run(
        ["git", "push", "-u", "origin", "main"], cwd=work, check=True, capture_output=True
    )
    return LocalBareRepoClient(str(remote), str(work))


def test_e2e_heal_critic_diff_pr_negative(tmp_path) -> None:
    orch = HealerOrchestrator()
    out = orch.heal_case(
        "renamed_ids:/login",
        "login",
        "renamed_ids",
        DRIFTED_HTML,
        ' id="login-submit"',
        ["login-submit"],
        "login-submit",
        baseline_html=BASE_HTML,
        key_elements=("login-submit",),
        purpose="submit",
    )
    assert out.healed == "login-submit"
    verdict = run_checks(
        DRIFTED_HTML,
        out.healed,
        "login-submit",
        BASE_HTML,
        ["login-submit"],
        [],
        ["demo", "wiremock"],
        "submit",
    )
    assert verdict.passed is True

    new_src, diff = edit_locator(SOURCE, "login-submit", "login-submit-v2")
    assert "login-submit-v2" in new_src
    body = build_pr_body(
        "heal login",
        diff,
        0.9,
        "pass",
        "rec",
        out.record.content_hash,
        "b.png",
        "a.png",
        "c.png",
        "sandbox://1",
        "revert X",
    )
    ok, missing = body_complete(body)
    assert ok and not missing

    client = repo(tmp_path)
    client.create_branch("heal/login-9")
    client.commit("heal/login-9", {"sample_test.py": new_src}, "heal login-submit")
    pr = client.open_pr("heal/login-9", "main", "Heal login", body, ["auto-heal"])
    assert pr.number == 1

    # Negative check: healed locator must FAIL against a seeded-defect build.
    bad = run_checks(
        REMOVED_HTML,
        "login-submit",
        "login-submit",
        BASE_HTML,
        ["login-submit"],
        [],
        ["demo", "wiremock"],
        "submit",
    )
    assert bad.passed is False  # would-be merge blocker if it passed

    # Self-approval never counts as the required review.
    assert reviews_valid(["heal-bot"], "heal-bot") is False


def test_e2e_genuine_regression_never_reaches_pr(tmp_path) -> None:
    orch = HealerOrchestrator()
    out = orch.heal_case(
        "removed_element:/login", "login", "removed_element", REMOVED_HTML, ' id="x"', [], None
    )
    assert out.healed is None and out.decision == "fail_escalate"
    assert out.shadow_pr is None
