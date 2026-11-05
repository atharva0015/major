"""Build one reproducible JSON transcript for the deterministic quality paths.

Covers the evidence that used to be test-only or documentation-only: PII
masking, narrative rendering, calibration, autonomy downgrade, survival
status, Prometheus metrics, assertion guard, AST locator diff, PR body,
shared-locator dedupe, the post-merge watcher, and a local bare-repo PR flow.

No Docker, browser, network, or real GitHub credentials are used. GitOps
runs against a temporary local bare repo. The output is a transcript, not a
live measurement.
"""

from __future__ import annotations

import dataclasses
import datetime
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

from prometheus_client import generate_latest

from healing.gitops.app import LocalBareRepoClient
from healing.gitops.ast_edit import edit_locator
from healing.gitops.dedupe import group_by_locator, plan_prs
from healing.gitops.pr_template import body_complete, build_pr_body
from healing.gitops.watch import on_failure, should_watch
from healing.nonui.assert_guard import guard_diff
from healing.quality.autonomy_guard import evaluate
from healing.quality.calibration import (
    alarm_if_diverged,
    expected_calibration_error,
    reliability_curve,
)
from healing.quality.observability import observe_ack, observe_escalation, observe_heal, traced
from healing.quality.survival import override_rate, revert_rate, survival_rate
from healing.security.masking import mask_mapping, mask_pii
from healing.xai.narrative import consistency_check, render_narrative
from healing.xai.records import make_record

OUT = os.path.join(
    "reports", "evidence", datetime.date.today().isoformat(), "quality_snapshot.json"
)
SAMPLE_TEST = os.path.join("healing", "gitops", "fixtures", "sample_test.py")


def _masking() -> dict[str, object]:
    masked = mask_pii(
        "contact ada@example.com, card 4111 1111 1111 1111, "
        "call +1 555-123-4567, Authorization: Bearer abc123XYZ"
    )
    return {
        "masked_text": masked,
        "mapping": mask_mapping({"email": "ada@example.com", "count": 3}),
        "markers": {
            "email": "[email]" in masked,
            "phone": "[phone]" in masked,
            "card": "[card]" in masked,
            "token": "[token]" in masked,
        },
    }


def _narrative() -> dict[str, object]:
    record = make_record(
        heal_id="heal-evidence-1",
        test="login",
        step="s1",
        classification="locator_drift",
        selected="login-submit",
        thresholds_applied={"high": 0.8},
        critic_checks={"verdict": "unverified"},
        escalation_reason=None,
        model_version="m",
        prompt_version="p",
        policy_version="pol",
        config_version="cfg",
    )
    text = render_narrative(record)
    return {
        "narrative": text,
        "consistency": consistency_check(text, record),
        "record_hash": record.content_hash,
    }


def _calibration() -> dict[str, object]:
    good = [(0.9, True)] * 9 + [(0.1, False)] * 9
    bad = [(0.95, False)] * 10
    good_ece = expected_calibration_error(good)
    bad_ece = expected_calibration_error(bad)
    return {
        "good_pairs_ece": good_ece,
        "good_alarm": alarm_if_diverged(good_ece, 0.15),
        "bad_pairs_ece": bad_ece,
        "bad_alarm": alarm_if_diverged(bad_ece, 0.15),
        "bad_reliability_curve": reliability_curve(bad),
    }


def _autonomy() -> dict[str, object]:
    verdict = evaluate(0.5, 0.0)
    return dataclasses.asdict(verdict)


def _survival() -> dict[str, object]:
    return {
        "30d": survival_rate([], 30),
        "revert": revert_rate([]),
        "override": override_rate([]),
    }


def _metrics() -> dict[str, object]:
    with traced("evidence.snapshot"):
        observe_heal(1, True, 0.05, 1.0)
        observe_escalation("locator_drift")
        observe_ack(12.0)
    text = generate_latest().decode("utf-8")
    lines = [
        ln
        for ln in text.splitlines()
        if ln.startswith(("heal_", "alert_"))
        or "heal_latency" in ln
        or "heal_cost" in ln
        or "heal_success" in ln
        or "heal_escalations" in ln
        or "alert_ack" in ln
    ]
    return {"prometheus_text": "\n".join(lines) + "\n"}


def _assertion_guard() -> list[dict[str, object]]:
    diffs = {
        "removed_assertion": "-    assert total == 10\n",
        "weakened_assertion": "+    assert total is not None\n",
        "threshold_change": "+    max_ms = 50\n",
        "safe_strengthening": "+    assert total == 11\n",
    }
    return [
        {"case": name, "diff": diff, "allowed": guard_diff(diff)[0], "reason": guard_diff(diff)[1]}
        for name, diff in diffs.items()
    ]


def _assert_under_temp(path: str) -> None:
    """Fail closed if a snapshot Git target is outside the OS temp directory."""
    root = Path(tempfile.gettempdir()).resolve()
    target = Path(path).resolve()
    if target != root and root not in target.parents:
        raise RuntimeError(f"refusing git path outside temp dir: {target}")


def _local_repo(tmp: str) -> LocalBareRepoClient:
    _assert_under_temp(tmp)
    remote, work = os.path.join(tmp, "r.git"), os.path.join(tmp, "w")
    _assert_under_temp(remote)
    _assert_under_temp(work)
    subprocess.run(["git", "init", "--bare", remote], cwd=tmp, check=True, capture_output=True)
    subprocess.run(["git", "clone", remote, work], cwd=tmp, check=True, capture_output=True)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=work, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=work, check=True)
    with open(SAMPLE_TEST, encoding="utf-8") as f:
        source = f.read()
    with open(os.path.join(work, "sample_test.py"), "w", encoding="utf-8") as f:
        f.write(source)
    subprocess.run(["git", "add", "."], cwd=work, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=work, check=True, capture_output=True)
    subprocess.run(
        ["git", "push", "-u", "origin", "main"], cwd=work, check=True, capture_output=True
    )
    return LocalBareRepoClient(remote, work)


def _gitops() -> dict[str, object]:
    with open(SAMPLE_TEST, encoding="utf-8") as f:
        source = f.read()
    new_source, diff = edit_locator(source, "login-submit", "login-submit-v2")
    body = build_pr_body(
        "Heal login locator drift",
        diff,
        0.93,
        "pass: all layers",
        "record:heal-evidence-1",
        "deadbeef",
        "shot://before",
        "shot://after",
        "shot://candidate",
        "replay://heal-evidence-1",
        "revert the PR",
    )
    complete, missing = body_complete(body)

    with tempfile.TemporaryDirectory() as tmp:
        client = _local_repo(tmp)
        client.create_branch("heal/login-7")
        sha = client.commit("heal/login-7", {"sample_test.py": new_source}, "heal login")
        pr = client.open_pr("heal/login-7", "main", "Heal login locator drift", body, ["auto-heal"])
        client.add_labels(pr, ["unverified", "needs-human"])
        client.comment(pr, "Critic pass; sandbox replay ok")

        # The post-merge watcher acts after the heal is merged.
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=client.workdir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "merge", "--no-ff", "heal/login-7", "-m", "merge heal"],
            cwd=client.workdir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=client.workdir,
            check=True,
            capture_output=True,
        )

        alerts: list[str] = []
        revert = on_failure("login", pr, "post-merge assertion failed", client, alerts.append)
        prs = [
            {
                "number": p.number,
                "branch": p.branch,
                "base": p.base,
                "title": p.title,
                "labels": p.labels,
                "comments": p.comments,
            }
            for p in client.prs
        ]

    return {
        "diff": diff,
        "new_source_has_locator": "login-submit-v2" in new_source,
        "pr_body": body,
        "pr_body_complete": complete,
        "pr_body_missing": missing,
        "branch_commit_sha": sha,
        "pull_requests": prs,
        "watch_now": should_watch(time.time(), 72),
        "watch_old": should_watch(time.time() - 100 * 3600.0, 72),
        "revert_record": revert,
        "alerts": alerts,
    }


def _dedupe() -> dict[str, object]:
    groups = group_by_locator(
        [
            {"test": "test_login", "locator": "login-submit"},
            {"test": "test_checkout", "locator": "login-submit"},
            {"test": "test_cart", "locator": "add-cart-1"},
        ]
    )
    return {"groups": groups, "plans": plan_prs(groups)}


def build_snapshot() -> dict[str, object]:
    return {
        "label": "SIMULATED/IN-PROCESS",
        "gitops_backend": "local bare repo (no network)",
        "masking": _masking(),
        "narrative": _narrative(),
        "calibration": _calibration(),
        "autonomy": _autonomy(),
        "survival": _survival(),
        "metrics": _metrics(),
        "assertion_guard": _assertion_guard(),
        "gitops": _gitops(),
        "dedupe": _dedupe(),
    }


def main() -> None:
    snapshot = build_snapshot()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"wrote {OUT}")
    print("sections: " + ", ".join(sorted(snapshot)))


if __name__ == "__main__":
    main()
