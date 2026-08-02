#!/usr/bin/env python3
"""
Venice Usage Dashboard Report Generator (starter template).
Read-only. Pulls billing/usage data via admin key and generates an HTML email report.
"""
import os
import sys
import json
import csv
import smtplib
import argparse
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import requests

ADMIN_KEY = os.environ.get("VENICE_ADMIN_KEY", "")
BASE_URL = "https://api.venice.ai/api/v1"
REPORT_DIR = Path.home() / ".venice_usage_reports"
ARCHIVE_FILE = REPORT_DIR / "usage_archive.jsonl"

# Safety: this key is only for read-only usage reporting.
# Any other use requires explicit user approval.


def api_get(path, params=None, key=ADMIN_KEY):
    url = f"{BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {key}"}
    r = requests.get(url, headers=headers, params=params, timeout=120)
    r.raise_for_status()
    return r.json()


def parse_sku(sku):
    """Parse a SKU into (category, token_type)."""
    sku_l = sku.lower()
    category = "unknown"
    if "llm" in sku_l:
        category = "llm"
    elif "image" in sku_l or "unit" in sku_l:
        category = "image"
    elif "video" in sku_l or "r2v" in sku_l:
        category = "video"
    elif "tts" in sku_l or "speech" in sku_l:
        category = "tts"
    elif "stt" in sku_l or "scribe" in sku_l or "whisper" in sku_l:
        category = "stt"
    elif "embedding" in sku_l:
        category = "embedding"
    elif "scrape" in sku_l or "search" in sku_l:
        category = "tool"

    token_type = None
    if category == "llm":
        if "cache-write" in sku_l:
            token_type = "Cache Write"
        elif "cache" in sku_l and "input" in sku_l:
            token_type = "Cache Read"
        elif "input" in sku_l:
            token_type = "Input"
        elif "output" in sku_l:
            token_type = "Output"
    return category, token_type


def fetch_all_data(lookback_days=2, archive=True):
    """Fetch all read-only data needed for the report."""
    data = {}
    data["balance"] = api_get("/billing/balance")
    data["keys"] = api_get("/api_keys")
    data["rate_limits"] = api_get("/api_keys/rate_limits")
    data["rate_limit_log"] = api_get("/api_keys/rate_limits/log")
    data["analytics_1d"] = api_get("/billing/usage-analytics", {"lookback": "1d"})
    data["analytics_7d"] = api_get("/billing/usage-analytics", {"lookback": "7d"})
    data["analytics_30d"] = api_get("/billing/usage-analytics", {"lookback": "30d"})
    data["models"] = api_get("/models", {"limit": 1000})

    since = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    usage = []
    page = 1
    while True:
        batch = api_get("/billing/usage", {"limit": 200, "page": page})
        items = batch.get("data", [])
        if not items:
            break
        usage.extend(items)
        oldest = datetime.fromisoformat(items[-1]["timestamp"].replace("Z", "+00:00"))
        if oldest < since:
            break
        if page >= batch.get("pagination", {}).get("totalPages", page):
            break
        page += 1
    data["usage_log"] = usage

    if archive:
        update_archive(usage)

    return data


def update_archive(usage_log):
    """Append new usage rows to JSONL archive, deduplicated by timestamp+sku+requestId."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    existing = set()
    if ARCHIVE_FILE.exists():
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    details = row.get("inferenceDetails") or {}
                    req_id = details.get("requestId") or ""
                    existing.add((row.get("timestamp"), row.get("sku"), req_id))
                except json.JSONDecodeError:
                    continue

    new_rows = 0
    with open(ARCHIVE_FILE, "a", encoding="utf-8") as f:
        for item in usage_log:
            details = item.get("inferenceDetails") or {}
            req_id = details.get("requestId") or ""
            key = (item.get("timestamp"), item.get("sku"), req_id)
            if key not in existing:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                new_rows += 1
    print(f"Archive updated: {new_rows} new rows added to {ARCHIVE_FILE}")


def summarize_analytics(analytics):
    total_diem = sum(d["DIEM"] for d in analytics.get("byDate", []))
    total_usd = sum(d["USD"] for d in analytics.get("byDate", []))
    by_model = sorted(analytics.get("byModel", []), key=lambda x: x["totalDiem"], reverse=True)
    by_key = sorted(analytics.get("byKey", []), key=lambda x: x["totalDiem"], reverse=True)
    return {
        "total_diem": total_diem,
        "total_usd": total_usd,
        "by_model": by_model,
        "by_key": by_key,
        "by_date": analytics.get("byDate", []),
    }


def build_key_map(keys_data):
    mapping = {}
    for k in keys_data.get("data", []):
        mapping[k["id"]] = {
            "description": k.get("description", "Unknown"),
            "type": k.get("apiKeyType", "INFERENCE"),
            "limits": k.get("consumptionLimits", {}),
            "limit_period": k.get("limitPeriod", "EPOCH"),
            "last_used": k.get("lastUsedAt"),
            "expires": k.get("expiresAt"),
            "trailing_7d": k.get("usage", {}).get("trailingSevenDays", {}),
            "current_period": k.get("usage", {}).get("currentPeriodUsage", {}),
        }
    return mapping


def format_diem(n):
    return f"{n:.6f}"


def format_usd(n):
    return f"${n:.6f}"


def build_html(data, report_date):
    summary_1d = summarize_analytics(data["analytics_1d"])
    summary_7d = summarize_analytics(data["analytics_7d"])
    summary_30d = summarize_analytics(data["analytics_30d"])
    key_map = build_key_map(data["keys"])
    balance = data["balance"]

    diem_balance = balance["balances"]["diem"]
    usd_balance = balance["balances"]["usd"]
    epoch_alloc = balance.get("diemEpochAllocation", 0)
    epoch_used_pct = ((epoch_alloc - diem_balance) / epoch_alloc * 100) if epoch_alloc else 0

    top_models_1d = summary_1d["by_model"][:10]
    top_keys_1d = summary_1d["by_key"][:10]

    yesterday = (report_date - timedelta(days=1)).date()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Venice Usage Dashboard — {report_date.strftime('%Y-%m-%d')}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#0f172a; color:#e2e8f0; margin:0; padding:20px; }}
  h1 {{ color:#38bdf8; }}
  h2 {{ color:#7dd3fc; border-bottom:1px solid #334155; padding-bottom:6px; margin-top:40px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; margin:20px 0; }}
  .card {{ background:#1e293b; border-radius:12px; padding:18px; }}
  .card .label {{ font-size:12px; text-transform:uppercase; color:#94a3b8; }}
  .card .value {{ font-size:28px; font-weight:700; color:#f8fafc; margin-top:6px; }}
  table {{ width:100%; border-collapse:collapse; margin:15px 0; font-size:13px; }}
  th {{ background:#334155; color:#f8fafc; padding:10px; text-align:left; }}
  td {{ padding:10px; border-bottom:1px solid #334155; }}
  .right {{ text-align:right; }}
</style>
</head>
<body>
<h1>Venice Usage Dashboard</h1>
<p>Report for {yesterday} · Generated {report_date.strftime('%Y-%m-%d %H:%M UTC')}</p>

<h2>Executive Summary</h2>
<div class="grid">
  <div class="card"><div class="label">24h DIEM Spend</div><div class="value">{format_diem(summary_1d['total_diem'])}</div></div>
  <div class="card"><div class="label">24h USD Spend</div><div class="value">{format_usd(summary_1d['total_usd'])}</div></div>
  <div class="card"><div class="label">DIEM Balance</div><div class="value">{format_diem(diem_balance)}</div></div>
  <div class="card"><div class="label">USD Balance</div><div class="value">{format_usd(usd_balance)}</div></div>
</div>

<h2>Top Models (24h)</h2>
<table>
  <tr><th>Model</th><th>Type</th><th>Units</th><th class="right">DIEM</th><th class="right">USD</th></tr>
"""
    for m in top_models_1d:
        html += f"""  <tr>
    <td>{m['modelName']}</td>
    <td>{m.get('modelType') or 'unknown'}</td>
    <td>{m['totalUnits']:.4f} {m.get('unitType','')}</td>
    <td class="right">{format_diem(m['totalDiem'])}</td>
    <td class="right">{format_usd(m['totalUsd'])}</td>
  </tr>
"""
    html += "</table>\n"

    html += """<h2>Top API Keys (24h)</h2>
<table>
  <tr><th>Key</th><th class="right">Units</th><th class="right">DIEM</th><th class="right">USD</th></tr>
"""
    for k in top_keys_1d:
        desc = key_map.get(k["apiKeyId"], {}).get("description", k["apiKeyId"][:8])
        html += f"""  <tr>
    <td>{desc}</td>
    <td class="right">{k['totalUnits']:.4f}</td>
    <td class="right">{format_diem(k['totalDiem'])}</td>
    <td class="right">{format_usd(k['totalUsd'])}</td>
  </tr>
"""
    html += "</table>\n"

    html += """</body>
</html>
"""
    return html


def save_csv(data, report_date):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = REPORT_DIR / f"venice_usage_{report_date.strftime('%Y%m%d_%H%M%S')}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "sku", "category", "currency", "amount", "units", "request_id", "prompt_tokens", "completion_tokens", "latency_ms"])
        for item in data["usage_log"]:
            cat, _ = parse_sku(item.get("sku", ""))
            details = item.get("inferenceDetails") or {}
            writer.writerow([
                item.get("timestamp"), item.get("sku"), cat, item.get("currency"),
                item.get("amount"), item.get("units"), details.get("requestId"),
                details.get("promptTokens"), details.get("completionTokens"),
                details.get("inferenceExecutionTime"),
            ])
    return csv_path


def send_email(html_path, csv_path, recipient, report_date):
    sender = os.environ.get("EMAIL_SENDER", "vivgatesai@gmail.com")
    password = os.environ.get("EMAIL_PASSWORD", "")
    if not password:
        print("EMAIL_PASSWORD not set; skipping email.")
        return False
    msg = MIMEMultipart()
    msg["From"] = f"Vega Usage Bot <{sender}>"
    msg["To"] = recipient
    msg["Subject"] = f"Venice Usage Dashboard — {report_date.strftime('%Y-%m-%d')}"
    msg.attach(MIMEText("<p>Your daily Venice usage dashboard is attached.</p>", "html"))

    for path in [html_path, csv_path]:
        with open(path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={path.name}")
        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
    print(f"Email sent to {recipient}")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default="vivek@live.de")
    parser.add_argument("--no-email", action="store_true")
    parser.add_argument("--lookback", type=int, default=2)
    args = parser.parse_args()

    if not ADMIN_KEY:
        print("VENICE_ADMIN_KEY environment variable is required.")
        sys.exit(1)

    report_date = datetime.now(timezone.utc)
    data = fetch_all_data(lookback_days=args.lookback, archive=True)
    html = build_html(data, report_date)
    html_path = REPORT_DIR / f"venice_dashboard_{report_date.strftime('%Y%m%d_%H%M%S')}.html"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    csv_path = save_csv(data, report_date)

    if not args.no_email:
        send_email(html_path, csv_path, args.email, report_date)


if __name__ == "__main__":
    main()
