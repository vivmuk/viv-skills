#!/usr/bin/env python3
"""
Generate an interactive HTML dashboard from a Venice usage_archive.jsonl file.

Output: ~/.venice_usage_reports/venice_usage_dashboard.html
Usage:
  python venice_usage_archive_dashboard.py --archive ~/.venice_usage_reports/usage_archive.jsonl
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def parse_dt(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)


def categorize(sku: str) -> str:
    if any(x in sku for x in ["promo", "credit-purchase", "venice-credit", "pro-user-api"]):
        return "credits"
    if "-llm-" in sku or "mtoken" in sku:
        return "llm"
    if any(x in sku for x in ["tts-", "stt-", "whisper", "parakeet", "kokoro", "voice-clone"]):
        return "audio"
    if any(x in sku for x in ["image-to-video", "text-to-video", "duration", "bytedance-pixel", "reference-to-video"]):
        return "video"
    if "image-unit" in sku or ("image" in sku and "-unit" in sku) or sku in ["grok-imagine-image", "gpt-image-1", "gpt-image-2"]:
        return "image"
    return "other"


def base_model(sku: str):
    if any(x in sku for x in ["promo", "credit-purchase", "venice-credit", "pro-user-api"]):
        return None
    if "-llm-" in sku:
        return sku.split("-llm-")[0]
    if "image-to-video" in sku or "text-to-video" in sku:
        return sku.split("-image-to-video")[0].split("-text-to-video")[0]
    if sku.startswith("tts-") or sku.startswith("stt-"):
        parts = sku.split("-")
        return "-".join(parts[:3]) if len(parts) >= 3 else sku
    return sku


def build_dashboard_data(archive_path: Path):
    records = [json.loads(line) for line in open(archive_path)]
    records.sort(key=lambda r: r["timestamp"])

    monthly = defaultdict(lambda: {"spend": 0.0, "requests": 0, "categories": defaultdict(float)})
    daily = defaultdict(float)
    model_alltime = defaultdict(lambda: {"spend": 0.0, "requests": 0, "category": ""})
    category_totals = defaultdict(float)

    for r in records:
        dt = parse_dt(r["timestamp"])
        sku = r["sku"]
        amt = r["amount"]
        base = base_model(sku)
        cat = categorize(sku)
        month = dt.strftime("%Y-%m")
        day = dt.strftime("%Y-%m-%d")

        monthly[month]["spend"] += amt
        monthly[month]["requests"] += 1
        monthly[month]["categories"][cat] += amt
        daily[day] += amt
        category_totals[cat] += amt

        if base:
            model_alltime[base]["spend"] += amt
            model_alltime[base]["requests"] += 1
            model_alltime[base]["category"] = cat

    sorted_days = sorted(daily.keys())
    rolling_7d = []
    for i, day in enumerate(sorted_days):
        window = sorted_days[max(0, i - 6):i + 1]
        avg = sum(daily[d] for d in window) / len(window)
        rolling_7d.append((day, avg))

    months = sorted(monthly.keys())
    categories = ["llm", "image", "video", "audio", "other"]
    cat_monthly = {cat: [monthly[m]["categories"].get(cat, 0) for m in months] for cat in categories}

    def top_by_category(cat, n=15):
        items = [(m, d) for m, d in model_alltime.items() if d["category"] == cat]
        return sorted(items, key=lambda x: x[1]["spend"])[:n]

    return {
        "months": months,
        "month_spend": [monthly[m]["spend"] for m in months],
        "month_requests": [monthly[m]["requests"] for m in months],
        "category_monthly": cat_monthly,
        "category_totals": {k: round(v, 2) for k, v in sorted(category_totals.items(), key=lambda x: -x[1])},
        "rolling": {"labels": [d for d, _ in rolling_7d[-60:]], "values": [round(v, 2) for _, v in rolling_7d[-60:]]},
        "top_models_overall": [
            {"name": m, "spend": round(d["spend"], 2), "requests": d["requests"], "category": d["category"]}
            for m, d in sorted(model_alltime.items(), key=lambda x: x[1]["spend"])[:50]
        ],
        "top_by_category": {
            cat: [
                {"name": m, "spend": round(d["spend"], 2), "requests": d["requests"]}
                for m, d in top_by_category(cat, 15)
            ]
            for cat in categories
        },
        "summary": {
            "total_records": len(records),
            "period_start": records[0]["timestamp"][:10],
            "period_end": records[-1]["timestamp"][:10],
            "total_spend": round(sum(monthly[m]["spend"] for m in months), 2),
            "total_requests": sum(monthly[m]["requests"] for m in months),
            "avg_7d": round(rolling_7d[-1][1], 2),
            "total_models": len(model_alltime),
            "latest_day": sorted_days[-1],
        }
    }


def render_table(rows):
    html = "<table><thead><tr><th>Rank</th><th>Model</th><th>Category</th><th>Requests</th><th>Spend</th></tr></thead><tbody>"
    for i, row in enumerate(rows, 1):
        cat = row.get("category", "")
        html += (
            f"<tr><td>{i}</td><td>{row['name']}</td>"
            f"<td><span class='badge badge-{cat}'>{cat}</span></td>"
            f"<td>{row['requests']:,}</td>"
            f"<td class='negative'>${abs(row['spend']):,.2f}</td></tr>"
        )
    html += "</tbody></table>"
    return html


def build_html(data):
    overall_table = render_table(data["top_models_overall"][:30])
    llm_table = render_table(data["top_by_category"]["llm"])
    image_table = render_table(data["top_by_category"]["image"])
    video_table = render_table(data["top_by_category"]["video"])
    audio_table = render_table(data["top_by_category"]["audio"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Venice Usage Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
:root{{--bg:#0b0f19;--card:#121929;--text:#e2e8f0;--muted:#94a3b8;--accent:#38bdf8;--green:#34d399;--red:#fb7185;--yellow:#facc15;--purple:#c084fc}}
*{{box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);margin:0;padding:24px;line-height:1.5}}
.container{{max-width:1400px;margin:0 auto}}
h1{{margin:0 0 8px;font-size:2rem}} p.subtitle{{color:var(--muted);margin:0 0 24px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:24px}}
.kpi{{background:var(--card);border:1px solid #1e293b;border-radius:12px;padding:18px}}
.kpi .label{{font-size:.85rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}}
.kpi .value{{font-size:1.8rem;font-weight:700;margin-top:6px}}
.kpi .negative{{color:var(--red)}} .kpi .positive{{color:var(--green)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(500px,1fr));gap:24px;margin-bottom:24px}}
.card{{background:var(--card);border:1px solid #1e293b;border-radius:12px;padding:20px}}
.card h2{{margin:0 0 16px;font-size:1.15rem;color:var(--text)}}
.chart-container{{position:relative;height:320px}}
table{{width:100%;border-collapse:collapse;font-size:.9rem}}
th,td{{text-align:left;padding:10px 8px;border-bottom:1px solid #1e293b}}
th{{color:var(--muted);font-weight:600;font-size:.8rem;text-transform:uppercase}}
tr:hover{{background:rgba(255,255,255,.03)}}
.badge{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:.75rem;font-weight:600}}
.badge-llm{{background:rgba(56,189,248,.15);color:var(--accent)}}
.badge-image{{background:rgba(192,132,252,.15);color:var(--purple)}}
.badge-video{{background:rgba(250,204,21,.15);color:var(--yellow)}}
.badge-audio{{background:rgba(52,211,153,.15);color:var(--green)}}
.badge-other{{background:rgba(148,163,184,.15);color:var(--muted)}}
.tabs{{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}}
.tab{{background:#1e293b;border:none;color:var(--text);padding:8px 14px;border-radius:8px;cursor:pointer;font-size:.9rem}}
.tab.active{{background:var(--accent);color:#0f172a;font-weight:600}}
.tab-content{{display:none}} .tab-content.active{{display:block}}
.full-width{{grid-column:1/-1}}
.small{{font-size:.8rem;color:var(--muted)}}
</style>
</head>
<body>
<div class="container">
<h1>🎭 Venice Usage Dashboard</h1>
<p class="subtitle">Comprehensive analysis from <strong>{data['summary']['period_start']}</strong> to <strong>{data['summary']['period_end']}</strong></p>

<div class="kpis">
<div class="kpi"><div class="label">Net Spend</div><div class="value negative">${abs(data['summary']['total_spend']):,.2f}</div></div>
<div class="kpi"><div class="label">Total Requests</div><div class="value">{data['summary']['total_requests']:,}</div></div>
<div class="kpi"><div class="label">Models Used</div><div class="value">{data['summary']['total_models']}</div></div>
<div class="kpi"><div class="label">7-Day Avg Spend</div><div class="value negative">${abs(data['summary']['avg_7d']):,.2f}/day</div></div>
</div>

<div class="grid">
<div class="card full-width">
<h2>Monthly Spend by Category</h2>
<div class="chart-container"><canvas id="monthlyChart"></canvas></div>
</div>

<div class="card full-width">
<h2>7-Day Rolling Average Spend</h2>
<div class="chart-container"><canvas id="rollingChart"></canvas></div>
</div>

<div class="card">
<h2>Spend by Category</h2>
<div class="chart-container"><canvas id="categoryChart"></canvas></div>
</div>

<div class="card">
<h2>Monthly Request Volume</h2>
<div class="chart-container"><canvas id="requestsChart"></canvas></div>
</div>
</div>

<div class="card full-width">
<h2>Top Models by Spend</h2>
<div class="tabs">
<button class="tab active" onclick="showTab('overall')">Overall</button>
<button class="tab" onclick="showTab('llm')">LLM/Text</button>
<button class="tab" onclick="showTab('image')">Image</button>
<button class="tab" onclick="showTab('video')">Video</button>
<button class="tab" onclick="showTab('audio')">Audio</button>
</div>
<div id="overall" class="tab-content active">{overall_table}</div>
<div id="llm" class="tab-content">{llm_table}</div>
<div id="image" class="tab-content">{image_table}</div>
<div id="video" class="tab-content">{video_table}</div>
<div id="audio" class="tab-content">{audio_table}</div>
</div>

<p class="small">Generated {data['summary']['latest_day']}. Data sourced from ~/.venice_usage_reports/usage_archive.jsonl.</p>
</div>

<script>
const months = {json.dumps(data['months'])};
const catMonthly = {json.dumps(data['category_monthly'])};
const monthRequests = {json.dumps(data['month_requests'])};
const rolling = {json.dumps(data['rolling'])};
const categoryTotals = {json.dumps(data['category_totals'])};

function fmt(n){{return '$'+Math.abs(n).toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}});}}

new Chart(document.getElementById('monthlyChart'),{{
  type:'bar',
  data:{{
    labels:months,
    datasets:[
      {{label:'LLM/Text',data:catMonthly.llm,backgroundColor:'#38bdf8'}},
      {{label:'Image',data:catMonthly.image,backgroundColor:'#c084fc'}},
      {{label:'Video',data:catMonthly.video,backgroundColor:'#facc15'}},
      {{label:'Audio',data:catMonthly.audio,backgroundColor:'#34d399'}},
      {{label:'Other',data:catMonthly.other,backgroundColor:'#94a3b8'}}
    ]
  }},
  options:{{responsive:true,maintainAspectRatio:false,scales:{{x:{{stacked:true}},y:{{stacked:true,ticks:{{callback:v=>'$'+Math.abs(v)}}}}}},plugins:{{tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+fmt(c.raw)}}}}}}}}
}});

new Chart(document.getElementById('rollingChart'),{{
  type:'line',
  data:{{
    labels:rolling.labels,
    datasets:[{{label:'7-Day Avg',data:rolling.values,borderColor:'#fb7185',backgroundColor:'rgba(251,113,133,0.1)',fill:true,tension:0.3,pointRadius:2}}]
  }},
  options:{{responsive:true,maintainAspectRatio:false,scales:{{y:{{ticks:{{callback:v=>'$'+Math.abs(v)}}}}}},plugins:{{tooltip:{{callbacks:{{label:c=>fmt(c.raw)+'/day'}}}}}}}}
}});

new Chart(document.getElementById('categoryChart'),{{
  type:'doughnut',
  data:{{
    labels:Object.keys(categoryTotals),
    datasets:[{{data:Object.values(categoryTotals),backgroundColor:['#38bdf8','#c084fc','#facc15','#34d399','#94a3b8','#fb7185']}}]
  }},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{tooltip:{{callbacks:{{label:c=>c.label+': '+fmt(c.raw)}}}}}}}}
}});

new Chart(document.getElementById('requestsChart'),{{
  type:'bar',
  data:{{labels:months,datasets:[{{label:'Requests',data:monthRequests,backgroundColor:'#38bdf8'}}]}},
  options:{{responsive:true,maintainAspectRatio:false,scales:{{y:{{ticks:{{callback:v=>(v/1000)+'k'}}}}}}}}
}});

function showTab(id){{
  document.querySelectorAll('.tab-content').forEach(el=>el.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(el=>el.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  event.target.classList.add('active');
}}
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=Path.home() / ".venice_usage_reports/usage_archive.jsonl")
    parser.add_argument("--output", type=Path, default=Path.home() / ".venice_usage_reports/venice_usage_dashboard.html")
    args = parser.parse_args()

    data = build_dashboard_data(args.archive)
    html = build_html(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html)
    print(f"Dashboard saved: {args.output}")


if __name__ == "__main__":
    main()
