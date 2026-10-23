#!/usr/bin/env python3
"""Fetch real public GitHub contribution counts and generate a README SVG preview."""
from __future__ import annotations
import json, re, urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from html import escape

USER = "gptshivam595"
ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (compatible; contribution-skyline/1.0)"
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#56d364"]

def get_text(url: str, accept: str = "text/html") -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")

def fetch_year(year: int) -> dict[str, int]:
    html = get_text(f"https://github.com/users/{USER}/contributions?from={year}-01-01&to={year}-12-31")
    tips = {}
    for element_id, count in re.findall(r'for="(contribution-day-component-[^"]+)"[^>]*>\s*(?:(\d+)\s+contributions?|No contributions)', html, re.I):
        tips[element_id] = int(count) if count else 0
    days = {}
    for day, element_id in re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"\s+id="(contribution-day-component-[^"]+)"', html):
        days[day] = tips.get(element_id, 0)
    if len(days) < 350 or len(tips) < 350:
        raise RuntimeError(f"Could not validate GitHub public contribution calendar for {year}: {len(days)} dates and {len(tips)} tooltips. Nothing was published.")
    return days

def quantile(values: list[int], p: float) -> int:
    return values[min(len(values)-1, int((len(values)-1)*p))] if values else 1

def level(count: int, cuts: list[int]) -> int:
    if count <= 0: return 0
    for i, cut in enumerate(cuts, 1):
        if count <= cut: return i
    return 5

def make_svg(payload: dict) -> str:
    days=payload["days"]; total=sum(int(d["count"]) for d in days)
    start=date.fromisoformat(days[0]["date"]); end=date.fromisoformat(days[-1]["date"])
    positive=sorted(int(d["count"]) for d in days if int(d["count"])>0)
    cuts=[quantile(positive,p) for p in (.25,.50,.75,.95)]
    weeks=[days[i:i+7] for i in range(0,len(days),7)]
    width,height=1100,224; cell,gap,left,top=12,4,72,88
    marks=[]; prev=""
    for wi,week in enumerate(weeks):
        if week:
            d=date.fromisoformat(week[0]["date"]); key=d.strftime("%Y-%m")
            if key != prev: marks.append((wi,d.strftime("%b"))); prev=key
    if len(marks)>1 and marks[1][0]-marks[0][0]<3: marks.pop(0)
    labels="".join(f'<text x="{left+w*(cell+gap)}" y="73" fill="#91a9c8" font-size="12">{escape(m)}</text>' for w,m in marks)
    rects=[]
    for i,d in enumerate(days):
        w,row=divmod(i,7); c=int(d["count"]); lv=level(c,cuts); x=left+w*(cell+gap); y=top+row*(cell+gap)
        rects.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{COLORS[lv]}" stroke="#8ddfff" stroke-opacity="{.42 if lv else .08}" stroke-width=".7"><title>{escape(d["date"])}: {c} contribution(s)</title></rect>')
    legend="".join(f'<rect x="{width-255+i*22}" y="192" width="13" height="13" rx="3" fill="{c}"/>' for i,c in enumerate(COLORS))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t d">
<title id="t">Shivam's public GitHub contribution heatmap</title><desc id="d">{total} public contributions from {start.isoformat()} through {end.isoformat()}. Click to open interactive 2D and 3D views.</desc>
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0b172a"/><stop offset="1" stop-color="#060b16"/></linearGradient><linearGradient id="edge" x1="0" x2="1"><stop stop-color="#38bdf8"/><stop offset="1" stop-color="#a78bfa"/></linearGradient></defs>
<rect width="100%" height="100%" rx="18" fill="url(#bg)"/><rect x="1" y="1" width="{width-2}" height="{height-2}" rx="17" fill="none" stroke="#274363"/>
<text x="26" y="27" fill="#55d8ff" font-size="10" font-weight="700" letter-spacing="2.3">PRODUCT MINDSET · CONSISTENT EXECUTION</text>
<text x="26" y="53" fill="#edf5ff" font-size="20" font-weight="700">{total:,} public contributions</text>
<text x="{width-26}" y="28" text-anchor="end" fill="#91a9c8" font-size="12">{start.strftime('%b %Y')} — {end.strftime('%b %Y')}</text>
<rect x="{width-223}" y="39" width="197" height="27" rx="13.5" fill="#10243c" stroke="#2a567d"/><text x="{width-124}" y="56" text-anchor="middle" fill="#bfeeff" font-size="10" font-weight="700">OPEN INTERACTIVE 2D / 3D ↗</text>
{labels}{''.join(rects)}
<text x="{left}" y="205" fill="#8199b9" font-size="10">Each square represents one day</text><text x="{width-280}" y="203" fill="#8199b9" font-size="10">Less</text>{legend}<text x="{width-26}" y="203" text-anchor="end" fill="#8199b9" font-size="10">More</text><path d="M26 218 H1074" stroke="url(#edge)" stroke-opacity=".55"/></svg>'''

def main() -> None:
    today=date.today(); start=today-timedelta(days=364); start-=timedelta(days=(start.weekday()+1)%7)
    profile=json.loads(get_text(f"https://api.github.com/users/{USER}","application/vnd.github+json"))
    counts={}
    for y in range(start.year,today.year+1): counts.update(fetch_year(y))
    days=[]; cursor=start
    while cursor<=today:
        key=cursor.isoformat(); days.append({"date":key,"count":int(counts.get(key,0))}); cursor+=timedelta(days=1)
    if len(days)<365: raise RuntimeError("Contribution data failed validation; refusing to publish an empty graph.")
    payload={"username":USER,"createdAt":profile.get("created_at","")[:10],"publicRepos":int(profile.get("public_repos") or 0),"start":days[0]["date"],"end":days[-1]["date"],"days":days,"total":sum(d["count"] for d in days),"updatedAt":datetime.utcnow().replace(microsecond=0).isoformat()+"Z"}
    site=ROOT/"site"; site.mkdir(parents=True,exist_ok=True)
    (site/"index.html").write_text((ROOT/"index.html").read_text(encoding="utf-8"),encoding="utf-8")
    (site/"contributions.json").write_text(json.dumps(payload,separators=(",",":"))+"\n",encoding="utf-8")
    assets=ROOT/"assets"; assets.mkdir(exist_ok=True)
    (assets/"contribution-preview.svg").write_text(make_svg(payload),encoding="utf-8")
    print(f"Generated {len(days)} dates from {payload['start']} to {payload['end']}; total={payload['total']}; public repositories={payload['publicRepos']}")

if __name__ == "__main__": main()
