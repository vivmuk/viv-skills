#!/usr/bin/env python3
"""
Weekly Activity Report Generator

Reads cumulative task CSV, filters for past 7 days,
generates an infographic via Venice gpt-image-2, and
outputs the image path + summary text for delivery.

Usage:
  python3 weekly_report.py

Input:
  ~/.hermes/weekly_tasks.csv  — CSV with columns: date,task,category,status,source

Output:
  Prints a summary with MEDIA: path for Telegram delivery.
  Saves infographic to ~/.hermes/weekly_infographic_<timestamp>.png
"""
import csv, json, base64, subprocess, os, sys
from datetime import datetime, timedelta

CSV_PATH = os.path.expanduser("~/.hermes/weekly_tasks.csv")
OUTPUT_DIR = os.path.expanduser("~/.hermes")
CONFIG_PATH = os.path.expanduser("~/.hermes/config.yaml")


def get_api_key():
    """Retrieve Venice API key from Hermes config."""
    result = subprocess.run(
        ["grep", "-A2", "api_key:", CONFIG_PATH],
        capture_output=True, text=True, timeout=5,
    )
    for line in result.stdout.split("\n"):
        if "VENICE" in line or "Kntg" in line:
            return line.split(":")[-1].strip().strip('"').strip("'")
    return None


def load_recent_tasks(days=7):
    """Load tasks from the past N days from the CSV."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    tasks = []
    if not os.path.exists(CSV_PATH):
        return tasks
    with open(CSV_PATH, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("date", "") >= cutoff:
                tasks.append(row)
    return tasks


def generate_infographic(tasks, api_key):
    """Generate an infographic image summarizing weekly tasks via Venice gpt-image-2."""
    # Group by category
    categories = {}
    for t in tasks:
        cat = t.get("category", "Other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(t.get("task", "")[:80])

    # Build prompt — must be <= 1500 chars for gpt-image-2
    now = datetime.now()
    week_ago = (now - timedelta(days=7)).strftime("%b %d")
    today = now.strftime("%b %d, %Y")

    prompt_parts = [
        f'Professional infographic: "GLM 5.1 Weekly Report {week_ago}-{today}". '
        f"Dark navy background, gold/teal/coral accents. "
    ]
    for cat, items in categories.items():
        count = len(items)
        prompt_parts.append(f"{cat} ({count} tasks). ")
    prompt_parts.append("Modern dashboard design with icons, progress bars, clean typography.")

    prompt = " ".join(prompt_parts)[:1499]

    payload = {
        "prompt": prompt,
        "model": "gpt-image-2",
        "n": 1,
        "response_format": "b64_json",
    }

    result = subprocess.run(
        [
            "curl", "-s",
            "https://api.venice.ai/api/v1/images/generations",
            "-H", f"Authorization: Bearer ***            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload),
        ],
        capture_output=True, text=True, timeout=300,
    )

    try:
        data = json.loads(result.stdout)
        if "data" in data and len(data["data"]) > 0:
            b64 = data["data"][0].get("b64_json", "")
            if b64:
                img_bytes = base64.b64decode(b64)
                ts = now.strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(OUTPUT_DIR, f"weekly_infographic_{ts}.png")
                with open(output_path, "wb") as f:
                    f.write(img_bytes)
                return output_path, None
    except Exception as e:
        return None, f"Image generation error: {e}"

    return None, "No image data returned"


def main():
    tasks = load_recent_tasks(days=7)
    if not tasks:
        print("No tasks found for the past week.")
        return

    api_key = get_api_key()
    if not api_key:
        print("ERROR: Could not find Venice API key in Hermes config")
        return

    img_path, error = generate_infographic(tasks, api_key)
    if error:
        print(f"ERROR: {error}")
        return

    # Build summary
    categories = {}
    for t in tasks:
        cat = t.get("category", "Other")
        categories.setdefault(cat, 0)
        categories[cat] += 1

    now = datetime.now()
    week_ago = (now - timedelta(days=7)).strftime("%b %d")
    today = now.strftime("%b %d, %Y")

    summary = f"📊 GLM 5.1 Weekly Report ({week_ago} - {today})\n\n"
    summary += f"Total tasks: {len(tasks)}\n\n"
    for cat, count in sorted(categories.items()):
        summary += f"• {cat}: {count}\n"
    summary += f"\nMEDIA:{img_path}"

    print(summary)


if __name__ == "__main__":
    main()
