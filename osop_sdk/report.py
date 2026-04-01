"""
OSOP Report Generators (HTML + Text)

HTML: Zero icons, zero JS, 5-color system, <15KB output.
      Uses native <details>/<summary> for expand/collapse.
      Dark mode via CSS prefers-color-scheme.

Text: Plain ASCII + optional ANSI color. <2KB output.
"""

from __future__ import annotations

import json
from html import escape as _h
from typing import Any

import yaml

# ============================================================
# Types (plain dicts — no pydantic dependency)
# ============================================================

# We work with raw dicts from yaml.safe_load; type aliases for readability.
Osop = dict[str, Any]
OsopLog = dict[str, Any]
LogRecord = dict[str, Any]

# ============================================================
# 5-color system
# ============================================================

TYPE_COLOR: dict[str, str] = {
    "human": "#ea580c", "agent": "#7c3aed",
    "api": "#2563eb", "mcp": "#2563eb", "cli": "#2563eb",
    "git": "#475569", "docker": "#475569", "cicd": "#475569",
    "system": "#475569", "infra": "#475569", "gateway": "#475569",
    "db": "#059669", "data": "#059669",
    "company": "#ea580c", "department": "#ea580c", "event": "#475569",
}


def _type_color(t: str) -> str:
    return TYPE_COLOR.get(t, "#475569")


# ============================================================
# Shared helpers
# ============================================================

def _ms(v: int | float | None) -> str:
    if v is None:
        return "-"
    if v < 1000:
        return f"{int(v)}ms"
    if v < 60000:
        return f"{v / 1000:.1f}s"
    return f"{v / 60000:.1f}m"


def _usd(v: float | None) -> str:
    if not v:
        return "$0"
    return f"${v:.4f}" if v < 0.01 else f"${v:.3f}"


def _kv_table(obj: Any) -> str:
    if not obj or not isinstance(obj, dict):
        return ""
    if len(obj) == 0:
        return ""
    rows: list[str] = []
    for k, v in obj.items():
        val = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
        display = val[:97] + "..." if len(val) > 100 else val
        rows.append(f"<tr><td>{_h(str(k))}</td><td>{_h(display)}</td></tr>")
    return "<table>" + "".join(rows) + "</table>"


# ============================================================
# HTML Report
# ============================================================

_CSS = (
    "*{margin:0;padding:0;box-sizing:border-box}"
    ":root{--ok:#16a34a;--err:#dc2626;--warn:#d97706;--bg:#fff;--fg:#1e293b;--mu:#64748b;--bd:#e2e8f0;--cd:#f8fafc}"
    "@media(prefers-color-scheme:dark){:root{--bg:#0f172a;--fg:#e2e8f0;--mu:#94a3b8;--bd:#334155;--cd:#1e293b}}"
    "body{font:14px/1.6 system-ui,sans-serif;background:var(--bg);color:var(--fg);max-width:800px;margin:0 auto;padding:16px}"
    "h1{font-size:1.4rem;font-weight:700}"
    ".st{display:flex;gap:12px;flex-wrap:wrap;margin:6px 0}.st span{font-weight:600}"
    ".s{padding:2px 8px;border-radius:3px;color:#fff;font-size:12px}.s.ok{background:var(--ok)}.s.err{background:var(--err)}"
    ".desc{color:var(--mu);font-size:13px;margin:4px 0}"
    ".meta{font:11px monospace;color:var(--mu);margin:4px 0}"
    ".eb{background:#fef2f2;border:1px solid #fecaca;color:var(--err);padding:8px 12px;border-radius:6px;margin:12px 0;font-size:13px}"
    "@media(prefers-color-scheme:dark){.eb{background:#450a0a;border-color:#7f1d1d}}"
    ".n{border:1px solid var(--bd);border-radius:6px;margin:8px 0;overflow:hidden}"
    ".n summary{display:flex;align-items:center;gap:8px;padding:8px 12px;cursor:pointer;background:var(--cd);font-size:13px;list-style:none}"
    ".n summary::-webkit-details-marker{display:none}"
    ".n.er{border-left:3px solid var(--err)}"
    ".tp{color:#fff;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.03em}"
    ".du{margin-left:auto;color:var(--mu);font-size:12px;font-family:monospace}"
    ".br{height:4px;border-radius:2px;display:inline-block;min-width:2px}"
    ".bd{padding:12px;font-size:13px;border-top:1px solid var(--bd)}"
    ".bd p{color:var(--mu);margin-bottom:8px}"
    ".bd table{width:100%;font-size:12px;border-collapse:collapse}"
    ".bd td{padding:3px 8px;border-bottom:1px solid var(--bd);vertical-align:top}"
    ".bd td:first-child{font-weight:600;color:var(--mu);width:30%;font-family:monospace;font-size:11px}"
    ".ai{font-size:12px;color:#7c3aed;margin-top:8px;font-family:monospace}"
    "@media(prefers-color-scheme:dark){.ai{color:#a78bfa}}"
    ".er-box{background:#fef2f2;color:var(--err);padding:8px;border-radius:4px;font-size:12px;margin-top:8px}"
    "@media(prefers-color-scheme:dark){.er-box{background:#450a0a}}"
    ".rt{font-size:12px;color:var(--ok);margin-top:4px}"
    "footer{text-align:center;padding:20px 0;color:var(--mu);font-size:11px}"
    "footer a{color:#2563eb}"
)


def generate_html_report(
    osop_yaml: str,
    osoplog_yaml: str | None = None,
    *,
    title: str | None = None,
) -> str:
    """Generate a self-contained HTML report from OSOP + optional log YAML strings."""
    o: Osop = yaml.safe_load(osop_yaml) or {}
    log: OsopLog | None = yaml.safe_load(osoplog_yaml) if osoplog_yaml else None
    is_exec = log is not None
    report_title = title or o.get("name") or o.get("id") or "OSOP Report"

    # Build latest record per node
    latest: dict[str, LogRecord] = {}
    failures: list[LogRecord] = []
    if log and log.get("node_records"):
        for r in log["node_records"]:
            prev = latest.get(r["node_id"])
            if prev is None or r["attempt"] > prev["attempt"]:
                latest[r["node_id"]] = r
            if r["status"] == "FAILED":
                failures.append(r)

    total_ms = log.get("duration_ms") if log else None
    body = ""

    # Header
    body += "<header>"
    body += f"<h1>{_h(report_title)}</h1>"
    body += '<div class="st">'
    if is_exec and log:
        sc = "ok" if log.get("status") == "COMPLETED" else "err"
        body += f'<span class="s {sc}">{_h(log.get("status", "UNKNOWN"))}</span>'
        body += f"<span>{_ms(log.get('duration_ms'))}</span>"
        cost_total = (log.get("cost") or {}).get("total_usd")
        if cost_total:
            body += f"<span>{_usd(cost_total)}</span>"
        body += f"<span>{len(latest)} nodes</span>"
    else:
        nodes = o.get("nodes") or []
        edges = o.get("edges") or []
        body += f"<span>{len(nodes)} nodes</span>"
        body += f"<span>{len(edges)} edges</span>"
        if o.get("version"):
            body += f'<span>v{_h(o["version"])}</span>'
    body += "</div>"
    if o.get("description"):
        body += f'<p class="desc">{_h(o["description"])}</p>'

    # Meta line
    meta: list[str] = []
    if o.get("id"):
        meta.append(o["id"])
    if log and log.get("run_id"):
        meta.append("run:" + log["run_id"][:8])
    if log and log.get("mode"):
        meta.append(log["mode"])
    if log and (log.get("runtime") or {}).get("agent"):
        meta.append(log["runtime"]["agent"])
    if log and (log.get("trigger") or {}).get("actor"):
        meta.append(log["trigger"]["actor"])
    if log and log.get("started_at"):
        meta.append(str(log["started_at"]).replace("T", " ").replace("Z", ""))
    if meta:
        body += f'<div class="meta">{" &middot; ".join(_h(m) for m in meta)}</div>'
    body += "</header>"

    # Error banner
    if failures:
        for f in failures:
            l = latest.get(f["node_id"])
            retried_ok = l is not None and l["status"] == "COMPLETED" and l["attempt"] > f["attempt"]
            err = f.get("error") or {}
            body += f'<div class="eb">{_h(f["node_id"])} failed: {_h(err.get("code", ""))} — {_h(err.get("message", "unknown"))}'
            if retried_ok:
                body += " — retried ok"
            body += "</div>"

    # Nodes
    body += "<main>"
    nodes = o.get("nodes") or []
    sorted_nodes = sorted(
        nodes,
        key=lambda n: 0 if latest.get(n["id"], {}).get("status") == "FAILED" else 1,
    )

    for node in sorted_nodes:
        rec = latest.get(node["id"])
        all_recs = [r for r in (log or {}).get("node_records", []) if r["node_id"] == node["id"]]
        is_failed = rec is not None and rec.get("status") == "FAILED"
        has_retry = len(all_recs) > 1
        cls = "n er" if is_failed else "n"
        open_attr = " open" if is_failed else ""

        body += f'<details class="{cls}"{open_attr}>'
        body += "<summary>"
        body += f'<span class="tp" style="background:{_type_color(node["type"])}">{_h(node["type"].upper())}</span>'
        body += f"<strong>{_h(node['name'])}</strong>"
        if rec:
            body += f'<span class="du">{_ms(rec.get("duration_ms"))}</span>'
            if rec["status"] == "COMPLETED":
                pct = max(1, round((rec.get("duration_ms") or 0) / total_ms * 100)) if total_ms else 0
                body += f'<span class="br" style="width:{pct}%;background:var(--ok)"></span>'
            elif rec["status"] == "FAILED":
                body += '<span class="s err">FAILED</span>'
            else:
                body += f'<span class="s ok">{_h(rec["status"])}</span>'
        body += "</summary>"

        body += '<div class="bd">'
        if node.get("description"):
            body += f"<p>{_h(node['description'])}</p>"

        inputs = (rec or {}).get("inputs") or node.get("inputs")
        outputs = (rec or {}).get("outputs") or node.get("outputs")
        if inputs:
            body += _kv_table(inputs)
        if outputs:
            body += _kv_table(outputs)

        # AI metadata
        ai = (rec or {}).get("ai_metadata")
        if ai:
            parts: list[str] = []
            if ai.get("model"):
                parts.append(ai["model"])
            if ai.get("prompt_tokens") is not None:
                parts.append(f"{ai['prompt_tokens']:,}->{ai.get('completion_tokens', 0):,} tok")
            if ai.get("cost_usd"):
                parts.append(_usd(ai["cost_usd"]))
            if ai.get("confidence") is not None:
                parts.append(f"{ai['confidence'] * 100:.0f}%")
            if parts:
                body += f'<div class="ai">{" &middot; ".join(_h(p) for p in parts)}</div>'

        # Human metadata
        hm = (rec or {}).get("human_metadata")
        if hm:
            parts = []
            if hm.get("actor"):
                parts.append(hm["actor"])
            if hm.get("decision"):
                parts.append("decision=" + hm["decision"])
            if hm.get("notes"):
                parts.append(hm["notes"])
            if parts:
                body += f'<div style="font-size:12px;color:var(--mu);margin-top:4px">{" &middot; ".join(_h(p) for p in parts)}</div>'

        # Tools used
        tools = (rec or {}).get("tools_used")
        if tools:
            body += f'<div style="font-size:12px;color:var(--mu);margin-top:4px">{", ".join(_h(t["tool"]) + "x" + str(t["calls"]) for t in tools)}</div>'

        # Error
        err = (rec or {}).get("error")
        if err:
            body += f'<div class="er-box">{_h(err["code"])}: {_h(err["message"])}'
            if err.get("details"):
                body += f"<br>{_h(err['details'])}"
            body += "</div>"

        # Retry history
        if has_retry:
            for r in all_recs:
                if r is rec:
                    continue
                body += f'<div class="rt">Attempt {r["attempt"]}: {_h(r["status"])} {_ms(r.get("duration_ms"))}'
                if r.get("error"):
                    body += f' — {_h(r["error"]["code"])}'
                body += "</div>"

        body += "</div></details>"

    body += "</main>"

    if log and log.get("result_summary"):
        body += f'<p style="margin:16px 0;padding:12px;background:var(--cd);border-radius:6px;font-size:13px;color:var(--mu)">{_h(log["result_summary"])}</p>'

    body += '<footer>OSOP v1.0 &middot; <a href="https://osop.ai">osop.ai</a></footer>'

    return (
        f'<!DOCTYPE html><html><head><meta charset="UTF-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{_h(report_title)}</title><style>{_CSS}</style></head>"
        f"<body>{body}</body></html>"
    )


# ============================================================
# Text Report
# ============================================================

# ANSI codes
_R = "\x1b[31m"
_G = "\x1b[32m"
_Y = "\x1b[33m"
_B = "\x1b[34m"
_M = "\x1b[35m"
_O = "\x1b[38;5;208m"
_D = "\x1b[2m"
_BO = "\x1b[1m"
_X = "\x1b[0m"

_TYPE_ANSI: dict[str, str] = {
    "human": _O, "agent": _M, "api": _B, "mcp": _B, "cli": _B,
    "git": _D, "docker": _D, "cicd": _D, "system": _D, "infra": _D, "gateway": _D,
    "db": _G, "data": _G, "company": _O, "event": _D,
}


def _pad(s: str, length: int) -> str:
    return s + " " * max(0, length - len(s))


def _dots(name: str, max_len: int) -> str:
    return name + " " + "." * max(2, max_len - len(name)) + " "


def generate_text_report(
    osop_yaml: str,
    osoplog_yaml: str | None = None,
    ansi: bool = False,
) -> str:
    """Generate a plain-text (or ANSI-colored) report from OSOP + optional log YAML strings."""
    o: Osop = yaml.safe_load(osop_yaml) or {}
    log: OsopLog | None = yaml.safe_load(osoplog_yaml) if osoplog_yaml else None

    def c(code: str, text: str) -> str:
        return code + text + _X if ansi else text

    lines: list[str] = []
    report_title = o.get("name") or o.get("id") or "OSOP Report"
    lines.append(c(_BO, f"OSOP Report: {report_title}"))
    lines.append("=" * min(60, len(report_title) + 14))

    if log:
        status = log.get("status", "UNKNOWN")
        sc = c(_G, "COMPLETED") if status == "COMPLETED" else c(_R, status)
        parts = [f"Status: {sc}", _ms(log.get("duration_ms"))]
        cost_total = (log.get("cost") or {}).get("total_usd")
        if cost_total:
            parts.append(f"${cost_total:.3f}")
        latest: dict[str, LogRecord] = {}
        for r in log.get("node_records") or []:
            prev = latest.get(r["node_id"])
            if prev is None or r["attempt"] > prev["attempt"]:
                latest[r["node_id"]] = r
        parts.append(f"{len(latest)} nodes")
        lines.append(" | ".join(parts))

        log_meta: list[str] = []
        if log.get("run_id"):
            log_meta.append("Run: " + log["run_id"][:8])
        if (log.get("runtime") or {}).get("agent"):
            log_meta.append("Agent: " + log["runtime"]["agent"])
        if (log.get("trigger") or {}).get("actor"):
            log_meta.append("Actor: " + log["trigger"]["actor"])
        if log_meta:
            lines.append(c(_D, " | ".join(log_meta)))

        # Errors first
        failures = [r for r in (log.get("node_records") or []) if r["status"] == "FAILED"]
        if failures:
            lines.append("")
            for f in failures:
                l = latest.get(f["node_id"])
                retried = l is not None and l["status"] == "COMPLETED" and l["attempt"] > f["attempt"]
                suffix = c(_G, " -> retried ok") if retried else ""
                err = f.get("error") or {}
                lines.append(
                    c(_R, f'! {f["node_id"]} FAILED (attempt {f["attempt"]})')
                    + f' -> {err.get("code", "")}: {err.get("message", "")}{suffix}'
                )

        # Node list
        lines.append("")
        nodes = o.get("nodes") or []
        max_name = max((len(n["id"]) for n in nodes), default=10)
        max_name = max(max_name, 10)
        dot_len = max_name + 4

        for node in nodes:
            rec = latest.get(node["id"])
            if not rec:
                continue
            tc = _TYPE_ANSI.get(node["type"], _D)
            type_str = _pad(node["type"].upper(), 7)
            name_str = _dots(node["id"], dot_len)
            dur_str = _pad(_ms(rec.get("duration_ms")), 7)

            node_status = c(_G, "ok") if rec["status"] == "COMPLETED" else c(_R, rec["status"])
            extras: list[str] = []

            if len([r for r in (log.get("node_records") or []) if r["node_id"] == node["id"]]) > 1:
                extras.append("(retry)")
            ai = rec.get("ai_metadata")
            if ai:
                if ai.get("prompt_tokens") is not None:
                    extras.append(f"{ai['prompt_tokens']:,}->{ai.get('completion_tokens', 0):,} tok")
                if ai.get("cost_usd"):
                    extras.append(f"${ai['cost_usd']:.3f}")
                if ai.get("confidence") is not None:
                    extras.append(f"{ai['confidence'] * 100:.0f}%")
            if (rec.get("human_metadata") or {}).get("decision"):
                extras.append("decision=" + rec["human_metadata"]["decision"])

            extra_str = "  " + c(_D, "  ".join(extras)) if extras else ""
            line = f"  {c(tc, type_str)} {name_str}{dur_str} {node_status}{extra_str}"
            lines.append(line)

        if log.get("result_summary"):
            lines.append("")
            lines.append(c(_D, "Summary: " + log["result_summary"]))
    else:
        # Spec mode
        nodes = o.get("nodes") or []
        edges = o.get("edges") or []
        lines.append(f"{len(nodes)} nodes, {len(edges)} edges")
        lines.append("")
        for node in nodes:
            tc = _TYPE_ANSI.get(node["type"], _D)
            lines.append(f"  {c(tc, _pad(node['type'].upper(), 7))} {node['name']}")

    lines.append("")
    return "\n".join(lines)
