#!/usr/bin/env python3
"""Fetch public GitHub contribution counts and build the README heatmap preview."""
from __future__ import annotations
import re, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from html import escape

USER = "gptshivam595"
ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (compatible; contribution-heatmap/1.0)"
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

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

def date_label(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"{parsed.strftime('%b')} {parsed.day}"

def streak_stats(days: list[dict]) -> tuple[dict, dict]:
    longest = {"days": 0, "start": None, "end": None}
    run = 0
    start = None
    for day in days:
        if day["count"] > 0:
            if run == 0:
                start = day["date"]
            run += 1
            if run > longest["days"]:
                longest = {"days": run, "start": start, "end": day["date"]}
        else:
            run = 0
    end = len(days) - 1
    if end >= 0 and days[end]["count"] == 0:
        end -= 1
    cursor = end
    while cursor >= 0 and days[cursor]["count"] > 0:
        cursor -= 1
    current = (
        {"days": end - cursor, "start": days[cursor + 1]["date"], "end": days[end]["date"]}
        if end >= 0 else {"days": 0, "start": None, "end": None}
    )
    return longest, current

def make_preview(payload: dict) -> str:
    days = payload["days"]
    positive = sorted(d["count"] for d in days if d["count"] > 0)
    cuts = [quantile(positive, p) for p in (.25, .5, .75, .95)]
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)]
    width, height, cell, gap, left, top = 1100, 305, 13, 4, 72, 82
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
            f' stroke="#0d1117" stroke-width=".7"><title>{escape(day["date"])}: {day["count"]} contribution(s)</title></rect>'
        )
    total = payload["total"]
    busiest = max(days, key=lambda day: day["count"])
    longest, current = streak_stats(days)
    start_label = date_label(payload["start"])
    end_label = date_label(payload["end"])
    longest_range = f"{date_label(longest['start'])} — {date_label(longest['end'])}" if longest["start"] else "—"
    current_range = f"{date_label(current['start'])} — {date_label(current['end'])}" if current["start"] else "—"
    stats = [
        ("1 year total", f"{total:,}", "contributions", f"{start_label} — {end_label}"),
        ("Busiest day", f"{busiest['count']:,}", "contributions", date_label(busiest["date"])),
        ("Longest streak", f"{longest['days']:,}", "days", longest_range),
        ("Current streak", f"{current['days']:,}", "days", current_range),
    ]
    stat_markup = []
    for index, (label, value, unit, sub) in enumerate(stats):
        x = 26 + index * 265
        stat_markup.append(
            f'<text x="{x}" y="222" fill="#8b949e" font-size="13" font-family="Arial,sans-serif">{label}</text>'
            f'<text x="{x}" y="253" fill="#39d353" font-size="29" font-weight="700" font-family="Arial,sans-serif">{value}</text>'
            f'<text x="{x + 82}" y="253" fill="#f0f6fc" font-size="15" font-family="Arial,sans-serif">{unit}</text>'
            f'<text x="{x}" y="273" fill="#8b949e" font-size="12" font-family="Arial,sans-serif">{escape(sub)}</text>'
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Shivam's GitHub contribution heatmap</title>
<desc id="desc">{total} contributions in the last year, shown as a dark GitHub-style calendar heatmap.</desc>
<rect width="100%" height="100%" rx="18" fill="#0d1117"/><rect x="1" y="1" width="{width-2}" height="{height-2}" rx="17" fill="none" stroke="#30363d"/>
<text x="26" y="37" fill="#f0f6fc" font-size="19" font-family="Arial,sans-serif"><tspan font-weight="700">{total:,}</tspan> contributions in the last year</text>
{labels}{''.join(rects)}
{''.join(stat_markup)}
<text x="26" y="294" fill="#8b949e" font-size="12" font-family="Arial,sans-serif">Actual public GitHub activity · refreshed automatically</text>
<text x="865" y="294" fill="#8b949e" font-size="12" font-family="Arial,sans-serif">Less</text>
{''.join(f'<rect x="{900 + i*20}" y="285" width="13" height="13" rx="3" fill="{color}"/>' for i, color in enumerate(COLORS))}
<text x="1020" y="294" fill="#8b949e" font-size="12" font-family="Arial,sans-serif">More</text></svg>'''

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
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    (assets / "contribution-preview.svg").write_text(make_preview(payload), encoding="utf-8")
    print(f"Generated {len(days)} dates from {payload['start']} to {payload['end']}; total={payload['total']}")

if __name__ == "__main__":
    main()
