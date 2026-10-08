"""PR body builder: summary, diff, confidence, verdict, evidence, rollback."""

from __future__ import annotations


def build_pr_body(
    summary: str,
    diff: str,
    confidence: float,
    critic_verdict: str,
    record_link: str,
    record_hash: str,
    before_shot: str,
    after_shot: str,
    candidate_shot: str,
    replay_link: str,
    rollback: str,
    decision: str = "heal_unverified",
) -> str:
    label = "verified" if decision == "heal_pr" else "unverified"
    return (
        f"## Auto-heal summary\n\n{summary}\n\n"
        f"## Diff\n\n```diff\n{diff}\n```\n\n"
        f"## Confidence\n\n{confidence:.3f}\n\n"
        f"## Critic verdict\n\n{critic_verdict}\n\n"
        f"## Explanation record\n\n{record_link} (hash `{record_hash}`)\n\n"
        f"## Screenshots\n\n"
        f"- before: {before_shot}\n- after: {after_shot}\n"
        f"- candidate highlighted: {candidate_shot}\n\n"
        f"## Sandbox replay\n\n{replay_link}\n\n"
        f"## Rollback\n\n{rollback}\n\n"
        f"<!-- labels: auto-heal, {label}, needs-human -->\n"
    )


REQUIRED_SECTIONS = (
    "## Auto-heal summary",
    "## Diff",
    "## Confidence",
    "## Critic verdict",
    "## Explanation record",
    "## Screenshots",
    "## Sandbox replay",
    "## Rollback",
)


def body_complete(body: str) -> tuple[bool, list[str]]:
    missing = [s for s in REQUIRED_SECTIONS if s not in body]
    return (not missing, missing)
