"""Read-only local dashboard for gates, explanation records, and metrics.

The page only reads files. It never heals, writes, approves, or opens PRs.
Displayed text is PII-masked and HTML-escaped. Bind it to localhost.
"""

from __future__ import annotations

import html
import json
import os
import re
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from healing.security.masking import mask_pii
from healing.xai.records import ExplanationRecord, verify_hash
from scripts import check_gates

DEFAULT_RECORDS = os.path.join("benchmark", "reports", "records.jsonl")
DEFAULT_LIMIT = 25
GATE_CACHE_SECONDS = 30.0

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": (
        "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"
    ),
}

app = FastAPI(
    title="Self-Healing MVP Dashboard",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

_gate_cache: tuple[float, list[dict[str, Any]]] | None = None


def _record_limit() -> int:
    try:
        value = int(os.getenv("DASHBOARD_RECORD_LIMIT", str(DEFAULT_LIMIT)))
    except ValueError:
        return DEFAULT_LIMIT
    return max(1, min(value, 100))


def _record_path() -> str:
    return os.getenv("RECORDS_PATH", DEFAULT_RECORDS)


def _metrics_path() -> str | None:
    explicit = os.getenv("DASHBOARD_METRICS_PATH")
    if explicit:
        return explicit
    root = Path("reports") / "evidence"
    if not root.exists():
        return None
    candidates = sorted(root.glob("*/quality_snapshot.json"))
    return str(candidates[-1]) if candidates else None


def _gate_rows() -> list[dict[str, Any]]:
    """Evaluate gates once per cache window; show an error row instead of crashing."""
    global _gate_cache
    now = time.monotonic()
    if _gate_cache is not None and now - _gate_cache[0] < GATE_CACHE_SECONDS:
        return _gate_cache[1]
    try:
        rows = check_gates.evaluate()
    except Exception as exc:  # dashboard must stay up; fail closed as UNVERIFIED
        rows = [
            {
                "metric": "gates",
                "op": "n/a",
                "target": None,
                "provenance": "config",
                "status": "UNVERIFIED",
                "actual": None,
                "message": f"UNVERIFIED gates: {exc}",
                "source": check_gates.TARGETS_MD,
            }
        ]
    _gate_cache = (now, rows)
    return rows


def _summarize_record(record: ExplanationRecord) -> dict[str, Any]:
    decision = "heal" if record.selected and not record.escalation_reason else "escalate"
    return {
        "heal_id": record.heal_id,
        "test": mask_pii(record.test),
        "step": mask_pii(record.step),
        "classification": mask_pii(record.classification),
        "selected": mask_pii(record.selected) if record.selected else None,
        "decision": decision,
        "critic": str(record.critic_checks.get("verdict", "n/a")),
        "escalation_reason": (
            mask_pii(record.escalation_reason) if record.escalation_reason else None
        ),
        "hash": record.content_hash[:12],
        "hash_ok": verify_hash(record),
    }


def load_records(path: str | None = None, limit: int | None = None) -> dict[str, Any]:
    """Read the newest records; malformed lines are counted, not rendered."""
    path = path or _record_path()
    limit = limit or _record_limit()
    if not os.path.exists(path):
        return {
            "available": False,
            "path": path,
            "records": [],
            "invalid": 0,
            "seen": 0,
            "limit": limit,
        }

    tail: deque[str] = deque(maxlen=limit)
    seen = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                seen += 1
                tail.append(line)

    records: list[dict[str, Any]] = []
    invalid = 0
    for line in tail:
        try:
            records.append(_summarize_record(ExplanationRecord.model_validate_json(line)))
        except (ValueError, TypeError):
            invalid += 1
    records.reverse()
    return {
        "available": True,
        "path": path,
        "records": records,
        "invalid": invalid,
        "seen": seen,
        "limit": limit,
    }


_SAMPLE_RE = re.compile(
    r"^(?P<name>[A-Za-z_:][A-Za-z0-9_:]*)(?P<labels>\{[^}]*\})?\s+(?P<value>\S+)$"
)
_LABEL_RE = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)="((?:[^"\\]|\\.)*)"')


def _parse_prometheus(text: str) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = _SAMPLE_RE.match(line)
        if not match:
            continue
        try:
            value = float(match.group("value"))
        except ValueError:
            continue
        labels = dict(_LABEL_RE.findall(match.group("labels") or ""))
        samples.append({"name": match.group("name"), "labels": labels, "value": value})
    return samples


def _sum_samples(samples: list[dict[str, Any]], name: str, **labels: str) -> float:
    total = 0.0
    for sample in samples:
        if sample["name"] != name:
            continue
        sample_labels = sample["labels"]
        if all(sample_labels.get(k) == v for k, v in labels.items()):
            total += float(sample["value"])
    return total


def load_metrics(path: str | None = None) -> dict[str, Any]:
    """Read the latest saved Prometheus transcript; never scrape a live process."""
    path = path or _metrics_path()
    if not path or not os.path.exists(path):
        return {
            "available": False,
            "path": path,
            "label": "",
            "error": "no saved metrics snapshot",
            "totals": {},
            "samples": [],
            "text": "",
        }
    try:
        with open(path, encoding="utf-8") as f:
            snapshot = json.load(f)
        metrics = snapshot.get("metrics", {}) if isinstance(snapshot, dict) else {}
        text = metrics.get("prometheus_text", "") if isinstance(metrics, dict) else ""
        if not isinstance(text, str):
            text = ""
        label = str(snapshot.get("label", "")) if isinstance(snapshot, dict) else ""
    except (OSError, ValueError, TypeError) as exc:
        return {
            "available": False,
            "path": path,
            "label": "",
            "error": str(exc),
            "totals": {},
            "samples": [],
            "text": "",
        }

    samples = _parse_prometheus(text)
    latency_count = _sum_samples(samples, "heal_latency_seconds_count")
    latency_sum = _sum_samples(samples, "heal_latency_seconds_sum")
    ack_count = _sum_samples(samples, "alert_ack_seconds_count")
    ack_sum = _sum_samples(samples, "alert_ack_seconds_sum")
    totals = {
        "heal_success": _sum_samples(samples, "heal_success_total", result="success"),
        "heal_fail": _sum_samples(samples, "heal_success_total", result="fail"),
        "escalations": _sum_samples(samples, "heal_escalations_total"),
        "cost": _sum_samples(samples, "heal_cost_total"),
        "latency_count": latency_count,
        "avg_latency_ms": (latency_sum / latency_count * 1000.0) if latency_count else None,
        "ack_count": ack_count,
        "avg_ack_s": (ack_sum / ack_count) if ack_count else None,
    }
    return {
        "available": True,
        "path": path,
        "label": label,
        "error": "",
        "totals": totals,
        "samples": samples,
        "text": text,
    }


def build_summary() -> dict[str, Any]:
    gates = _gate_rows()
    records = load_records()
    metrics = load_metrics()
    recent = records["records"]
    heals = sum(1 for record in recent if record["decision"] == "heal")
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read_only": True,
        "gates": gates,
        "gate_counts": {
            "pass": sum(1 for gate in gates if gate["status"] == "PASS"),
            "fail": sum(1 for gate in gates if gate["status"] == "FAIL"),
            "unverified": sum(1 for gate in gates if gate["status"] == "UNVERIFIED"),
        },
        "records": records,
        "record_counts": {
            "heals": heals,
            "escalations": len(recent) - heals,
            "hash_mismatch": sum(1 for record in recent if not record["hash_ok"]),
        },
        "metrics": metrics,
    }


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _number(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else f"{value:.4g}"
    return str(value)


def _badge(status: str) -> str:
    css = {"PASS": "pass", "FAIL": "fail", "UNVERIFIED": "unverified"}.get(status, "unknown")
    return f'<span class="badge {css}">{_escape(status)}</span>'


def _gate_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<p class="muted">No gate rows available.</p>'
    body = "".join(
        "<tr>"
        f"<td><code>{_escape(row['metric'])}</code></td>"
        f"<td><code>{_escape(row['op'])} {_escape(row['target'])}</code></td>"
        f"<td>{_escape(_number(row['actual']))}</td>"
        f"<td>{_badge(str(row['status']))}</td>"
        f"<td>{_escape(row['provenance'])}</td>"
        f'<td class="detail">{_escape(row["message"])}</td>'
        "</tr>"
        for row in rows
    )
    return (
        '<div class="scroll"><table><thead><tr>'
        "<th>Metric</th><th>Target</th><th>Actual</th><th>Status</th>"
        "<th>Provenance</th><th>Detail</th>"
        f"</tr></thead><tbody>{body}</tbody></table></div>"
    )


def _record_table(records: list[dict[str, Any]]) -> str:
    if not records:
        return '<p class="muted">No explanation records found.</p>'
    body = "".join(
        "<tr>"
        f"<td><code>{_escape(record['heal_id'])}</code></td>"
        f"<td>{_escape(record['test'])}</td>"
        f"<td>{_escape(record['step'])}</td>"
        f'<td><span class="badge {record["decision"]}">{_escape(record["decision"])}</span></td>'
        f"<td>{_escape(record['classification'])}</td>"
        f"<td><code>{_escape(record['selected'] or '—')}</code></td>"
        f"<td>{_escape(record['critic'])}</td>"
        f"<td>{_badge('PASS' if record['hash_ok'] else 'FAIL')}</td>"
        "</tr>"
        for record in records
    )
    return (
        '<div class="scroll"><table><thead><tr>'
        "<th>Heal ID</th><th>Test</th><th>Step</th><th>Decision</th>"
        "<th>Class</th><th>Selected</th><th>Critic</th><th>Hash</th>"
        f"</tr></thead><tbody>{body}</tbody></table></div>"
    )


def _metric_cards(metrics: dict[str, Any]) -> str:
    if not metrics["available"]:
        return (
            '<p class="muted">No metrics snapshot: '
            f"{_escape(metrics['path'] or 'not configured')} "
            f"({_escape(metrics['error'])})</p>"
        )
    totals = metrics["totals"]
    cards = [
        ("Successful heals", _number(totals.get("heal_success"))),
        ("Failed heals", _number(totals.get("heal_fail"))),
        ("Escalations", _number(totals.get("escalations"))),
        ("Cost units", _number(totals.get("cost"))),
        ("Latency samples", _number(totals.get("latency_count"))),
        (
            "Avg latency",
            "—" if totals.get("avg_latency_ms") is None else f"{totals['avg_latency_ms']:.2f} ms",
        ),
        ("Alert acks", _number(totals.get("ack_count"))),
        (
            "Avg ack",
            "—" if totals.get("avg_ack_s") is None else f"{totals['avg_ack_s']:.2f} s",
        ),
    ]
    body = "".join(
        f'<div class="mini"><span>{_escape(label)}</span><strong>{_escape(value)}</strong></div>'
        for label, value in cards
    )
    return (
        f'<div class="mini-grid">{body}</div>'
        f'<p class="muted">Source: <code>{_escape(metrics["path"])}</code>'
        f" · label: <code>{_escape(metrics['label'] or 'n/a')}</code></p>"
        "<details><summary>Raw Prometheus transcript</summary>"
        f"<pre>{_escape(metrics['text'])}</pre></details>"
    )


def render_page(summary: dict[str, Any]) -> str:
    gates = summary["gates"]
    gate_counts = summary["gate_counts"]
    records = summary["records"]
    record_counts = summary["record_counts"]
    metrics = summary["metrics"]

    warnings = []
    if not records["available"]:
        warnings.append(f"Records file not found: {records['path']}")
    if records["invalid"]:
        warnings.append(
            f"{records['invalid']} malformed record line(s) skipped in the latest window"
        )
    if not metrics["available"]:
        warnings.append(f"Metrics snapshot unavailable: {metrics['path'] or 'not configured'}")
    if record_counts["hash_mismatch"]:
        warnings.append(
            f"{record_counts['hash_mismatch']} recent record(s) failed hash verification"
        )
    warning_html = (
        '<div class="warning"><strong>Data warnings</strong><ul>'
        + "".join(f"<li>{_escape(item)}</li>" for item in warnings)
        + "</ul></div>"
        if warnings
        else ""
    )

    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Self-Healing MVP Dashboard</title>"
        f"<style>{_STYLE}</style></head><body>"
        "<header><div><h1>Self-Healing MVP</h1>"
        '<p class="sub">Gates, explanation records, and the latest saved metrics snapshot. '
        "Local files only.</p></div>"
        '<span class="badge read-only">READ-ONLY</span></header>'
        "<main>"
        f'<section class="cards">'
        f'<div class="card"><span>Quality gates</span><strong>{gate_counts["pass"]} PASS</strong>'
        f"<small>{gate_counts['fail']} FAIL · {gate_counts['unverified']} UNVERIFIED</small></div>"
        f'<div class="card"><span>Recent records</span><strong>{len(records["records"])}</strong>'
        f"<small>{record_counts['heals']} heals · "
        f"{record_counts['escalations']} escalations</small></div>"
        f'<div class="card"><span>Record integrity</span>'
        f"<strong>{record_counts['hash_mismatch']} mismatch</strong>"
        f"<small>hash-checked on read</small></div>"
        f'<div class="card"><span>Metrics source</span>'
        f"<strong>{'saved snapshot' if metrics['available'] else 'unavailable'}</strong>"
        f"<small>{_escape(metrics['label'] or 'no label')}</small></div>"
        "</section>"
        f"{warning_html}"
        '<section><div class="section-head"><h2>Quality gates</h2>'
        '<span class="muted">recomputed from reports; cached 30s</span></div>'
        f"{_gate_table(gates)}</section>"
        '<section><div class="section-head"><h2>Recent explanation records</h2>'
        f'<span class="muted">newest {_escape(records["limit"])} of {_escape(records["seen"])} · '
        f"{_escape(records['path'])}</span></div>"
        f"{_record_table(records['records'])}</section>"
        '<section><div class="section-head"><h2>Metrics snapshot</h2>'
        '<span class="muted">not live; no Prometheus scrape</span></div>'
        f"{_metric_cards(metrics)}</section>"
        "</main>"
        f"<footer>Generated {_escape(summary['generated_at'])} · read-only · "
        "bind to 127.0.0.1 · no auth, do not expose publicly</footer>"
        "</body></html>"
    )


_STYLE = """
:root{color-scheme:light;--ink:#17202a;--muted:#5d6d7e;--line:#d6dbdf;--bg:#f4f6f7;
--card:#fff;--pass:#1e8449;--fail:#b03a2e;--unverified:#9a7d0a;--accent:#1f618d}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;
background:var(--bg);color:var(--ink)}header{display:flex;justify-content:space-between;
gap:16px;align-items:flex-start;padding:24px 32px;background:var(--ink);color:#fff}
h1{margin:0;font-size:26px}h2{font-size:18px;margin:0}.sub{margin:4px 0 0;color:#d5dbdb}
main{max-width:1400px;margin:0 auto;padding:24px 32px 40px}section{margin:0 0 28px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}
.card,.mini{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}
.card span,.mini span{display:block;color:var(--muted);font-size:13px}
.card strong{display:block;font-size:24px;margin:4px 0}.card small{color:var(--muted)}
.section-head{display:flex;justify-content:space-between;gap:12px;align-items:baseline;
margin:0 0 10px}.muted{color:var(--muted);font-size:13px}
.scroll{overflow:auto;border:1px solid var(--line);border-radius:10px;background:var(--card)}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:9px 12px;
border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#eaecee;font-size:12px;text-transform:uppercase;letter-spacing:.03em;
white-space:nowrap}tr:last-child td{border-bottom:0}td.detail{color:var(--muted);
min-width:280px}code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:13px}
.badge{display:inline-block;border-radius:999px;padding:2px 9px;font-size:12px;
font-weight:700;letter-spacing:.03em;white-space:nowrap}
.badge.pass,.badge.heal{background:#d4efdf;color:var(--pass)}
.badge.fail,.badge.escalate{background:#fadbd8;color:var(--fail)}
.badge.unverified{background:#fcf3cf;color:var(--unverified)}
.badge.read-only{background:#fff;color:var(--ink);align-self:center;padding:7px 12px}
.badge.unknown{background:#e5e8e8;color:var(--muted)}
.warning{background:#fef9e7;border:1px solid #f7dc6f;border-radius:10px;padding:12px 16px;
margin:0 0 24px}.warning ul{margin:6px 0 0;padding-left:20px}
.mini-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;
margin:0 0 10px}.mini strong{display:block;font-size:20px;margin-top:2px}
details{margin-top:10px}summary{cursor:pointer;color:var(--accent)}
pre{overflow:auto;background:#17202a;color:#eaf2f8;padding:14px;border-radius:8px;
font-size:12px;max-height:420px}footer{max-width:1400px;margin:0 auto;padding:0 32px 32px;
color:var(--muted);font-size:12px}@media(max-width:700px){header,main,footer{padding-left:16px;
padding-right:16px}h1{font-size:22px}}
"""


@app.get("/")
def index() -> HTMLResponse:
    return HTMLResponse(render_page(build_summary()), headers=SECURITY_HEADERS)


@app.get("/api/summary")
def api_summary() -> JSONResponse:
    return JSONResponse(build_summary(), headers=SECURITY_HEADERS)


@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok", "read_only": True}, headers=SECURITY_HEADERS)


def main() -> None:
    import uvicorn

    host = os.getenv("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.getenv("DASHBOARD_PORT", "8080"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
