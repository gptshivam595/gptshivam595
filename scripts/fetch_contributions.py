#!/usr/bin/env python3
"""Fetch public GitHub contribution counts and build the static heatmap data."""
from __future__ import annotations
import json, re, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from html import escape

USER = "gptshivam595"
ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (compatible; contribution-heatmap/1.0)"
COLORS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]

def get_text(url: str, accept: str = "text/html") -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=40) as response:
        return response.read().decode("utf-8", "replace")

def fetch_year(year: int) -> dict[str, int]:
    html = get_text(f"https://github.com/users/{USER}/contributions?from={year}-01-01&to={year}-12-31")
    tips = {}
    for element_id, count in re.findall(
        r'for="(contribution-day-component-[^"]+)"[^>]*>\s*(?:(\d+)\s+contributions?|No contributions)',
        html, re.I,
    ):
        tips[element_id] = int(count) if count else 0
    days = {
        day: tips.get(element_id, 0)
        for day, element_id in re.findall(
            r'data-date="(\d{4}-\d{2}-\d{2})"\s+id="(contribution-day-component-[^"]+)"',
            html,
        )
    }
    if len(days) < 350 or len(tips) < 350:
        raise RuntimeError(f"Could not validate GitHub contribution calendar for {year}.")
    return days

def quantile(values: list[int], proportion: float) -> int:
    return values[min(len(values) - 1, int((len(values) - 1) * proportion))] if values else 1

def level(count: int, cuts: list[int]) -> int:
    if count <= 0:
        return 0
    for index, cut in enumerate(cuts, 1):
        if count <= cut:
            return index
    return 4

def make_preview(payload: dict) -> str:
    days = payload["days"]
    positive = sorted(d["count"] for d in days if d["count"] > 0)
    cuts = [quantile(positive, p) for p in (.25, .5, .75, .95)]
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)]
    width, height, cell, gap, left, top = 1100, 225, 13, 4, 72, 76
    marks, previous = [], ""
    for week_index, week in enumerate(weeks):
        if week:
            key = week[0]["date"][:7]
            if key != previous:
                marks.append((week_index, date.fromisoformat(week[0]["date"]).strftime("%b")))
                previous = key
    labels = "".join(
        f'<text x="{left + week * (cell + gap)}" y="62" fill="#737373" font-size="12">{escape(label)}</text>'
        for week, label in marks
    )
    rects = []
    for index, day in enumerate(days):
        week, row = divmod(index, 7)
        x, y = left + week * (cell + gap), top + row * (cell + gap)
        rects.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{COLORS[level(day["count"], cuts)]}"'
            f' stroke="#ffffff" stroke-width=".7"><title>{escape(day["date"])}: {day["count"]} contribution(s)</title></rect>'
        )
    total = payload["total"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Shivam's GitHub contribution heatmap</title>
<desc id="desc">{total} contributions in the last year. Click to open the interactive heatmap.</desc>
<rect width="100%" height="100%" rx="16" fill="#fff"/><rect x="1" y="1" width="{width-2}" height="{height-2}" rx="15" fill="none" stroke="#e5e7eb"/>
<text x="24" y="31" fill="#171717" font-size="17" font-family="Arial,sans-serif"><tspan font-weight="700">{total:,}</tspan> contributions in the last year</text>
{labels}{''.join(rects)}
<text x="24" y="207" fill="#737373" font-size="11" font-family="Arial,sans-serif">Hover a day for details</text>
<text x="865" y="207" fill="#737373" font-size="11" font-family="Arial,sans-serif">Less</text>
{''.join(f'<rect x="{900 + i*20}" y="198" width="13" height="13" rx="3" fill="{color}"/>' for i, color in enumerate(COLORS))}
<text x="1020" y="207" fill="#737373" font-size="11" font-family="Arial,sans-serif">More</text></svg>'''

def main() -> None:
    today = date.today()
    start = today - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)
    counts = {}
    for year in range(start.year, today.year + 1):
        counts.update(fetch_year(year))
    days, cursor = [], start
    while cursor <= today:
        key = cursor.isoformat()
        days.append({"date": key, "count": int(counts.get(key, 0))})
        cursor += timedelta(days=1)
    if len(days) < 365:
        raise RuntimeError("Contribution data failed validation.")
    payload = {
        "username": USER, "start": days[0]["date"], "end": days[-1]["date"],
        "days": days, "total": sum(d["count"] for d in days),
        "updatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    site = ROOT / "site"
    site.mkdir(exist_ok=True)
    (site / "index.html").write_text((ROOT / "index.html").read_text(encoding="utf-8"), encoding="utf-8")
    (site / "contributions.json").write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    (assets / "contribution-preview.svg").write_text(make_preview(payload), encoding="utf-8")
    print(f"Generated {len(days)} dates from {payload['start']} to {payload['end']}; total={payload['total']}")

if __name__ == "__main__":
    main()
