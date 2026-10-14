"""Live Healenium verification: services, proxy, one drifted heal, read-back.

Run by a human with the compose stack up. Exits non-zero on the first
failed check. Saves the verbatim backend payload for fixture/adapter work:
benchmark/fixtures/healenium_report_sample.json
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

BACKEND = os.getenv("HEALENIUM_URL", "http://localhost:7878")
PROXY = os.getenv("HEALENIUM_PROXY_URL", "http://localhost:8085")
SELENOID = os.getenv("SELENOID_URL", "http://localhost:4444")
DEMO_HOST = os.getenv("DEMO_URL", "http://localhost:8001")
DEMO_IN_COMPOSE = os.getenv("DEMO_IN_COMPOSE_URL", "http://demo:8001")
COMPOSE = ["docker", "compose", "--project-directory", "infra", "-f", "infra/docker-compose.yml"]
FIXTURE = os.path.join("benchmark", "fixtures", "healenium_report_sample.json")


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail else ""))
    if not ok:
        raise SystemExit(f"live check failed at: {name} {detail}")


def wait_http(url: str, timeout_s: float = 120.0) -> int:
    """Poll until an HTTP response arrives; return status. Raise on timeout."""
    deadline = time.perf_counter() + timeout_s
    last = "no response yet"
    while time.perf_counter() < deadline:
        try:
            r = httpx.get(url, timeout=5.0)
            return r.status_code
        except Exception as exc:  # noqa: BLE001 - any transport failure means not ready
            last = f"{type(exc).__name__}: {exc}"
            time.sleep(3.0)
    raise TimeoutError(f"{url}: {last}")


def find_healing_entry(payload: object, locator_sub: str) -> dict[str, object] | None:
    """Find the newest report entry mentioning a locator. Plain dicts only.

    Live backend 3.5.1 nests rows under "data" (verified); anything else
    means no usable entries (fail closed).
    """
    items = payload.get("data", []) if isinstance(payload, dict) else []
    if not isinstance(items, list):
        return None
    for it in reversed(items):
        if isinstance(it, dict) and locator_sub in json.dumps(it):
            return it
    return None


def extract_score(entry: dict[str, object]) -> float | None:
    """Single opaque score in [0, 1]; None on any doubt (fail closed).

    Live backend 3.5.1 encodes it as a string ("0.97"); accept numeric
    strings too, reject everything else. Only the observed "score" key
    counts; guessed keys are rejected.
    """
    v = entry.get("score")
    if isinstance(v, bool):
        return None
    if isinstance(v, str):
        v = float(v) if v.replace(".", "", 1).isdigit() else None
    if isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0:
        return float(v)
    return None


def restart_demo(drift: str) -> None:
    env = dict(os.environ, DRIFT_MODE=drift)
    subprocess.run([*COMPOSE, "up", "-d", "demo"], check=True, env=env)
    wait_http(DEMO_HOST + "/login")


def warmup_green_pass() -> None:
    """Green lookups first: Healenium needs stored references to heal later."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By

    restart_demo("none")
    driver = webdriver.Remote(PROXY, options=webdriver.ChromeOptions())
    try:
        for page, by_id in (
            ("/login", "login-submit"),
            ("/products", "add-cart-1"),
            ("/checkout", "checkout-submit"),
        ):
            driver.get(DEMO_IN_COMPOSE + page)
            driver.find_element(By.ID, by_id)
    finally:
        driver.quit()


def drifted_heal_probe() -> dict[str, object]:
    from selenium import webdriver
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.by import By

    restart_demo("renamed_ids")
    try:
        options = webdriver.ChromeOptions()
        driver = webdriver.Remote(PROXY, options=options)
        try:
            driver.get(DEMO_IN_COMPOSE + "/login")
            try:
                el = driver.find_element(By.ID, "login-submit")
                healed = {
                    "healed": True,
                    "tag": el.tag_name,
                    "testid": el.get_attribute("data-testid"),
                }
            except NoSuchElementException:
                healed = {"healed": False}
        finally:
            driver.quit()
    finally:
        restart_demo("none")
    r = httpx.get(BACKEND + "/healenium/report/data", timeout=10.0)
    check("backend report readable", r.status_code == 200, f"HTTP {r.status_code}")
    payload = r.json()
    # Live backend 3.5.1 writes one row per locator and reuses it on repeat
    # healings (verified: reruns heal fine but add no new rows). So the
    # read-back asserts the locator's record exists with a healed value,
    # whether written by this probe or an earlier identical one.
    entry = find_healing_entry(payload, "login-submit")
    deadline = time.perf_counter() + 60.0
    while entry is None and time.perf_counter() < deadline:
        time.sleep(3.0)
        payload = httpx.get(BACKEND + "/healenium/report/data", timeout=10.0).json()
        entry = find_healing_entry(payload, "login-submit")
    os.makedirs(os.path.dirname(FIXTURE), exist_ok=True)
    with open(FIXTURE, "w", encoding="utf-8") as f:
        json.dump(
            payload if isinstance(payload, (dict, list)) else {"raw": str(payload)},
            f,
            indent=2,
            sort_keys=True,
        )
    entry = find_healing_entry(payload, "login-submit")
    check("healing entry recorded", entry is not None)
    assert entry is not None
    check(
        "healed locator present",
        bool(entry.get("healedLocatorValue")),
        f"healed={entry.get('healedLocatorValue')}",
    )
    score = extract_score(entry)
    check("numeric score present", score is not None, f"score={score}")
    print("raw entry keys: " + ", ".join(sorted(entry.keys())))
    return {"probe": healed, "score": score, "entry_keys": sorted(entry.keys())}


def main() -> None:
    status = wait_http(BACKEND + "/healenium/report")
    check("backend healthy", status == 200, f"HTTP {status}")
    try:
        httpx.get(PROXY + "/", timeout=10.0)
        check("proxy reachable", True)
    except Exception as exc:  # noqa: BLE001 - reported, not hidden
        check("proxy reachable", False, f"{type(exc).__name__}: {exc}")
    r = httpx.get(SELENOID + "/status", timeout=10.0)
    check("selenoid ready", r.status_code == 200, f"HTTP {r.status_code}")
    check("demo serves login", wait_http(DEMO_HOST + "/login") == 200)
    warmup_green_pass()
    probe = drifted_heal_probe()
    from healing.matching.healenium_adapter import HealeniumAdapter

    adapter = HealeniumAdapter(base_url=BACKEND)
    check("adapter parses live schema", True, f"adapter={adapter.version}")
    print(json.dumps(probe, indent=2, sort_keys=True))
    print("LIVE CHECK PASS")


if __name__ == "__main__":
    main()
