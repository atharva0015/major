"""Live Healenium bench: whole UI benchmark through the real proxy.

Requires the compose stack up and `pip install selenium`. A green warmup
stores Healenium reference selectors first (how the real tool works); then
per drift group the demo restarts with that DRIFT_MODE and each case gets
a fresh browser session through hlm-proxy with a naive By.ID lookup.

Outcome kinds: healed (returned id differs, proxy intervened),
passthrough (old id still resolves, no healing event), escalated
(NoSuchElementException). Correctness = resolved data-testid vs the
known-correct answer. Session order is recorded so cold-vs-warm effects
stay visible.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.cases import CASES
from healing.quality.metrics import RunResult, compute_metrics, to_markdown

PROXY = os.getenv("HEALENIUM_PROXY_URL", "http://localhost:8085")
DEMO_HOST = os.getenv("DEMO_URL", "http://localhost:8001")
DEMO_IN_COMPOSE = os.getenv("DEMO_IN_COMPOSE_URL", "http://demo:8001")
COMPOSE = ["docker", "compose", "--project-directory", "infra", "-f", "infra/docker-compose.yml"]
REPORT_MD = os.path.join("benchmark", "reports", "healenium_live.md")
REPORT_JSON = os.path.join("benchmark", "reports", "healenium_live.json")
LIVE_POLICY = "healenium-live-0.1.0"


def naive_id_from_locator(locator: str) -> str:
    """' id="login-submit"' -> 'login-submit'. Refuses anything else."""
    m = re.fullmatch(r'\s*id="([^"]+)"', locator)
    if not m:
        raise ValueError(f"not a plain id locator: {locator!r}")
    return m.group(1)


def restart_demo(drift: str) -> None:
    env = dict(os.environ, DRIFT_MODE=drift)
    subprocess.run([*COMPOSE, "up", "-d", "demo"], check=True, env=env)
    import httpx

    deadline = time.perf_counter() + 90.0
    while time.perf_counter() < deadline:
        try:
            if httpx.get(DEMO_HOST + "/login", timeout=5.0).status_code == 200:
                return
        except Exception:  # noqa: BLE001 - not ready yet
            time.sleep(2.0)
    raise TimeoutError("demo did not come back after drift switch")


def new_session():  # type: ignore[no-untyped-def]
    from selenium import webdriver

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    return webdriver.Remote(PROXY, options=options)


def run_case_live(case: object, session_no: int) -> dict[str, object]:
    """Drive one case through proxy + real browser. Returns a plain record."""
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.by import By

    naive_id = naive_id_from_locator(str(getattr(case, "locator")))
    page = str(getattr(case, "page"))
    correct = getattr(case, "correct_element")
    t0 = time.perf_counter()
    driver = new_session()
    try:
        driver.get(DEMO_IN_COMPOSE + page)
        try:
            el = driver.find_element(By.ID, naive_id)
            found_id = el.get_attribute("id") or ""
            testid = el.get_attribute("data-testid") or ""
            via = "healed" if found_id != naive_id else "passthrough"
        except NoSuchElementException:
            found_id, testid, via = "", "", "escalated"
    finally:
        driver.quit()
    latency_ms = (time.perf_counter() - t0) * 1000.0
    healed = via in ("healed", "passthrough")
    ok = healed and testid == correct
    return {
        "session_no": session_no,
        "case_id": getattr(case, "case_id"),
        "should_heal": bool(getattr(case, "should_heal")),
        "healed": healed,
        "correct": bool(ok),
        "escalated": via == "escalated",
        "via": via,
        "resolved_testid": testid,
        "latency_ms": latency_ms,
    }


def adversarial_block(results: list[RunResult]) -> str:
    adv = [r for r in results if not r.should_heal]
    healed = [r for r in adv if r.healed]
    wrong = [r for r in healed if not r.correct]
    rate = (len(wrong) / len(healed)) if healed else 0.0
    lines = [
        "## Adversarial cases (must NOT heal)",
        f"- adversarial total: {len(adv)}",
        f"- adversarial healed: {len(healed)}",
        f"- adversarial false heals: {len(wrong)}",
        f"- adversarial false-heal rate: {rate:.3f}",
        "",
        "| case | healed | escalated |",
        "|---|---|---|",
    ]
    for r in adv:
        lines.append(f"| {r.case_id} | {r.healed} | {r.escalated} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)
    by_drift: dict[str, list[object]] = {}
    for case in CASES:
        by_drift.setdefault(str(getattr(case, "drift_mode")), []).append(case)
    # Green warmup stores reference selectors (required by real Healenium).
    restart_demo("none")
    for page in ("/login", "/products", "/checkout"):
        driver = new_session()
        try:
            driver.get(DEMO_IN_COMPOSE + page)
        finally:
            driver.quit()
    results: list[RunResult] = []
    vias: list[dict[str, object]] = []
    session_no = 0
    for drift in sorted(by_drift):
        restart_demo(drift)
        for case in by_drift[drift]:
            session_no += 1
            rec = run_case_live(case, session_no)
            vias.append(rec)
            results.append(
                RunResult(
                    case_id=str(rec["case_id"]),
                    should_heal=bool(rec["should_heal"]),
                    healed=bool(rec["healed"]),
                    correct=bool(rec["correct"]),
                    escalated=bool(rec["escalated"]),
                    cost=1.0,
                    latency_ms=float(rec["latency_ms"]),
                )
            )
    metrics = compute_metrics(results)
    md = to_markdown(metrics, title="Healenium attempt-1 report (live)")
    md += f"\n- policy: {LIVE_POLICY}, seed: 42, live: True\n"
    md += "\n" + adversarial_block(results)
    md += "\n## Per-case results (via: healed | passthrough | escalated)\n\n"
    md += "| case | should_heal | healed | correct | via |\n|---|---|---|---|---|\n"
    for rec, r in zip(vias, results):
        md += (
            f"| {r.case_id} | {r.should_heal} | {r.healed} | {r.correct} | "
            f"{rec['via']} (session {rec['session_no']}) |\n"
        )
    md += (
        f"\nWarmup: one green pass over 3 pages before drift runs (Healenium "
        f"needs stored references). Expected: {len(CASES)} cases.\n"
    )
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    summary = {"metrics": vars(metrics), "vias": vias, "live": True, "policy": LIVE_POLICY}
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    print(md.strip())


if __name__ == "__main__":
    main()
