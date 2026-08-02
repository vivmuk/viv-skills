#!/usr/bin/env python3
"""Analyze a Venice usage archive JSONL.

Produces summary tables for:
- Overall totals and date range
- Monthly spend
- Last N days by category
- Top models/categories overall
- Today hourly breakdown

Usage:
  python analyze_venice_usage_archive.py --archive ~/.venice_usage_reports/usage_archive.jsonl
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


def parse_dt(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)


def categorize(sku: str) -> str:
    if "llm-" in sku or "mtoken" in sku:
        return "llm_text"
    if any(x in sku for x in ["tts-", "stt-", "whisper", "parakeet", "kokoro", "voice-clone"]):
        return "audio"
    if any(x in sku for x in ["image-to-video", "text-to-video", "duration", "bytedance-pixel", "reference-to-video"]):
        return "video"
    if "image-unit" in sku or ("image" in sku and "-unit" in sku) or sku in ["grok-imagine-image", "gpt-image-1", "gpt-image-2"]:
        return "image"
    if any(x in sku for x in ["promo", "credit-purchase", "venice-credit", "pro-user-api"]):
        return "credits"
    return "other"


def base_model(sku: str) -> str:
    if "-llm-" in sku:
        return sku.split("-llm-")[0]
    if "image-to-video" in sku or "text-to-video" in sku:
        return sku.split("-image-to-video")[0].split("-text-to-video")[0]
    return sku


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--last-days", type=int, default=30)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()

    records = [json.loads(line) for line in open(args.archive)]
    records.sort(key=lambda r: r["timestamp"])

    # overall
    net = sum(r["amount"] for r in records)
    credit = sum(r["amount"] for r in records if categorize(r["sku"]) == "credits")
    spend = net - credit
    start = parse_dt(records[0]["timestamp"])
    end = parse_dt(records[-1]["timestamp"])

    print(f"Records: {len(records):,}")
    print(f"Date range: {start.date()} -> {end.date()}")
    print(f"Net change: ${net:,.2f}")
    print(f"Credit purchases/promos: ${credit:,.2f}")
    print(f"Actual spend: ${spend:,.2f}\n")

    # monthly
    monthly = defaultdict(float)
    for r in records:
        if categorize(r["sku"]) == "credits":
            continue
        monthly[parse_dt(r["timestamp"]).strftime("%Y-%m")] += r["amount"]
    print("Monthly spend:")
    for month in sorted(monthly):
        print(f"  {month}: ${monthly[month]:10,.2f}")
    print()

    # last N days
    cutoff = end - timedelta(days=args.last_days)
    recent = [r for r in records if parse_dt(r["timestamp"]) >= cutoff]
    cats = defaultdict(lambda: {"spend": 0.0, "requests": 0})
    for r in recent:
        cat = categorize(r["sku"])
        if cat == "credits":
            continue
        cats[cat]["spend"] += r["amount"]
        cats[cat]["requests"] += 1
    print(f"Last {args.last_days} days (excl. credits):")
    print(f"  Records: {len(recent):,}")
    print(f"  Total: ${sum(v['spend'] for v in cats.values()):,.2f}")
    for cat, v in sorted(cats.items(), key=lambda x: -x[1]["spend"]):
        print(f"    {cat:12s} ${v['spend']:10,.2f}  ({v['requests']:,} requests)")
    print()

    # daily last 14 days
    daily = defaultdict(float)
    for r in records:
        if categorize(r["sku"]) == "credits":
            continue
        daily[parse_dt(r["timestamp"]).strftime("%Y-%m-%d")] += r["amount"]
    print("Daily spend (last 14 days):")
    for day in sorted(daily)[-14:]:
        print(f"  {day}: ${daily[day]:10,.2f}")
    print()

    # top models overall
    model_total = defaultdict(float)
    for r in records:
        if categorize(r["sku"]) == "credits":
            continue
        model_total[base_model(r["sku"])] += r["amount"]
    print(f"Top {args.top} most expensive models/categories (all time):")
    for model, amt in sorted(model_total.items(), key=lambda x: x[1])[:args.top]:
        print(f"  ${amt:12,.2f}  {model}")
    print()

    # today hourly
    today = end.date()
    hourly = defaultdict(lambda: {"spend": 0.0, "requests": 0, "cats": defaultdict(float)})
    for r in records:
        dt = parse_dt(r["timestamp"])
        if dt.date() != today:
            continue
        cat = categorize(r["sku"])
        hourly[dt.hour]["spend"] += r["amount"]
        hourly[dt.hour]["requests"] += 1
        hourly[dt.hour]["cats"][cat] += r["amount"]
    if hourly:
        print(f"Today ({today}) hourly:")
        print(f"  {'Hour':>5} {'Spend':>10} {'Reqs':>8} {'LLM':>10} {'Audio':>10} {'Video':>10} {'Image':>10} {'Other':>10}")
        for hour in sorted(hourly):
            h = hourly[hour]
            c = h["cats"]
            print(f"  {hour:5d} {h['spend']:10.2f} {h['requests']:8d} "
                  f"{c.get('llm_text', 0):10.2f} {c.get('audio', 0):10.2f} "
                  f"{c.get('video', 0):10.2f} {c.get('image', 0):10.2f} {c.get('other', 0):10.2f}")


if __name__ == "__main__":
    main()
