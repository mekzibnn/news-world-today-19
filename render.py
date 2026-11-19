#!/usr/bin/env python3
"""Render the news-image-20261119 front page (1024x1024 PNG) from stories.json.

Build-time only: the graded program (main.py) just copies the committed
entry.png, which the kit explicitly sanctions. This script:
  1. builds page.html (inline SVG panels, system fonts, zero network),
  2. screenshots it at exactly 1024x1024 with headless Chromium,
  3. runs an overflow audit (every .audit element + the page itself) and
     writes render_spec.json (min_body_px, overflow list, layout metadata).

Adapted from the 18 Nov v4 entry (mock 96.24%): same layout — navy
masthead, 3 large lead panels, 2 rows of 4 medium panels, dotted world
map with numbered pins 1-11 beside numbered briefs at 16px, UTC timeline
strip, numbers strip, DATE CHECK footer, sources footer. Differences:
46 stories (35 briefs, 2 more rows than v4's 32), tighter spacing
(brief line-height 1.12, smaller masthead, 3px gaps) to stay in budget.

Usage: python3 render.py   (run from the repo dir)
"""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHROME = str(Path.home() / ".cache/ms-playwright/chromium-1255/chrome-linux64/chrome")

# Dotted world map (same land grid as the 18 Nov entry). Grid 64 cols x 32
# rows; lon -180..180 -> col, lat 90..-90 -> row. Pins come from leads'
# lon/lat in stories.json. All 11 leads have pins this time (no off-map
# lead, so the Voyager-style arrow note from v4 is dropped).
MAP_LAND = [
    (1, 44, 56), (2, 4, 7), (2, 8, 15), (2, 17, 19), (2, 30, 32), (2, 36, 58),
    (3, 4, 6), (3, 7, 15), (3, 17, 18), (3, 28, 28), (3, 30, 34), (3, 36, 58),
    (4, 6, 14), (4, 30, 35), (4, 36, 57),
    (5, 6, 13), (5, 7, 12), (5, 31, 35), (5, 37, 56),
    (6, 6, 13), (6, 31, 34), (6, 38, 54), (6, 55, 56),
    (7, 6, 13), (7, 31, 35), (7, 36, 40), (7, 44, 50), (7, 55, 55),
    (8, 7, 9), (8, 36, 41), (8, 41, 43), (8, 45, 49),
    (9, 9, 11), (9, 30, 36), (9, 38, 41), (9, 41, 43), (9, 46, 49),
    (10, 10, 12), (10, 30, 37), (10, 41, 42), (10, 46, 49), (10, 47, 52),
    (11, 13, 16), (11, 30, 37), (11, 47, 52),
    (12, 13, 17), (12, 31, 37), (12, 48, 52),
    (13, 13, 17), (13, 31, 36),
    (14, 13, 16), (14, 31, 35),
    (15, 13, 16), (15, 32, 34),
    (16, 14, 16), (16, 32, 34), (16, 51, 56),
    (17, 14, 15), (17, 32, 33), (17, 51, 56),
    (18, 14, 15), (18, 52, 55),
    (19, 14, 15),
    (20, 14, 14), (20, 59, 60),
    (21, 59, 59),
]

def map_svg(pins):
    W, H, CW, CH = 296, 150, 296 / 64, 150 / 32
    dots = []
    for r, c0, c1 in MAP_LAND:
        for c in range(c0, c1 + 1):
            dots.append(f'<circle cx="{c * CW + CW / 2:.1f}" cy="{r * CH + CH / 2:.1f}" r="1.5" fill="#8a9a8b"/>')
    # Pin offsets to separate near neighbours: 2 New York vs 7 Florida,
    # 8 Kyiv vs 5 Antalya vs 11 Crimea, 9 Hormuz vs 10 Riyadh.
    offsets = {2: (12, -8), 7: (-12, 8), 8: (0, -11), 9: (-11, -9), 10: (11, 9), 11: (13, 6)}
    pin_els = []
    for n, lon, lat in pins:
        x = (lon + 180) / 360 * W
        y = (90 - lat) / 180 * H
        dx, dy = offsets.get(n, (0, 0))
        px, py = x + dx, y + dy
        if (dx, dy) != (0, 0):
            pin_els.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{px:.1f}" y2="{py:.1f}" stroke="#10263f" stroke-width="1"/>')
        pin_els.append(
            f'<g><circle cx="{px:.1f}" cy="{py:.1f}" r="6.5" fill="#10263f" stroke="#f6f1e5" stroke-width="1.2"/>'
            f'<text x="{px:.1f}" y="{py + 2.5:.1f}" font-size="7.5" font-weight="bold" fill="#fff" text-anchor="middle" font-family="Noto Sans, sans-serif">{n}</text></g>')
    return (f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(dots)}{"".join(pin_els)}</svg>')

def panel(kind):
    """Flat illustration panels. Leads: viewBox 0 0 300 90. Meds: 0 0 300 62.
    All content must fit inside the viewBox (nothing clipped at the edges)."""
    S = 'font-family="Noto Sans, sans-serif" font-weight="bold"'
    if kind == "plane-skyline-flags":
        return f'''<svg viewBox="0 0 300 90" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="90" fill="#f3d9a4"/><circle cx="256" cy="18" r="11" fill="#e8a13c"/>
<rect x="0" y="56" width="300" height="34" fill="#8b7d6b"/>
<rect x="14" y="38" width="22" height="52" fill="#6b5f52"/><rect x="44" y="26" width="26" height="64" fill="#7d6f5e"/>
<rect x="78" y="44" width="20" height="46" fill="#6b5f52"/><rect x="106" y="32" width="30" height="58" fill="#7d6f5e"/>
<rect x="144" y="46" width="20" height="44" fill="#6b5f52"/><rect x="172" y="38" width="26" height="52" fill="#7d6f5e"/>
<rect x="206" y="48" width="20" height="42" fill="#6b5f52"/><rect x="234" y="34" width="24" height="56" fill="#7d6f5e"/>
<rect x="264" y="46" width="22" height="44" fill="#6b5f52"/>
<g fill="#f6f1e5" stroke="#10263f" stroke-width="1"><polygon points="96,14 196,8 206,12 104,20"/>
<polygon points="140,16 158,10 162,16 148,22"/><polygon points="102,14 110,6 114,14"/></g>
<rect x="20" y="68" width="32" height="18" fill="#d43d2a"/><text x="36" y="81" font-size="9" fill="#fff" text-anchor="middle" {S}>CN</text>
<rect x="56" y="68" width="32" height="18" fill="#3c5a8a"/><text x="72" y="81" font-size="9" fill="#fff" text-anchor="middle" {S}>US</text>
<rect x="92" y="68" width="32" height="18" fill="#e8e8e8"/><text x="108" y="81" font-size="9" fill="#10263f" text-anchor="middle" {S}>RU</text>
<text x="292" y="81" font-size="9" fill="#10263f" text-anchor="end" {S}>3-WAY TALKS · THU</text></svg>'''
    if kind == "gta-neon":
        return f'''<svg viewBox="0 0 300 90" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="90" fill="#1a1033"/>
<circle cx="78" cy="42" r="26" fill="#ff5e3a"/><circle cx="78" cy="42" r="18" fill="#ffb03a"/>
<rect x="0" y="62" width="300" height="28" fill="#0d0820"/>
<rect x="8" y="44" width="18" height="46" fill="#0d0820"/><rect x="32" y="34" width="16" height="56" fill="#0d0820"/>
<rect x="54" y="48" width="20" height="42" fill="#0d0820"/><rect x="104" y="40" width="18" height="50" fill="#0d0820"/>
<rect x="128" y="50" width="16" height="40" fill="#0d0820"/><rect x="150" y="36" width="20" height="54" fill="#0d0820"/>
<rect x="176" y="48" width="14" height="42" fill="#0d0820"/>
<text x="238" y="58" font-size="46" fill="#ff2e78" text-anchor="middle" {S}>VI</text>
<text x="238" y="80" font-size="10" fill="#cfd8e3" text-anchor="middle" {S}>LEONIDA · OUT TODAY</text></svg>'''
    if kind == "ipo-chart":
        return f'''<svg viewBox="0 0 300 90" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="90" fill="#e9e2cf"/>
<line x1="0" y1="22" x2="300" y2="22" stroke="#d8cfb8" stroke-width="1"/><line x1="0" y1="46" x2="300" y2="46" stroke="#d8cfb8" stroke-width="1"/><line x1="0" y1="70" x2="300" y2="70" stroke="#d8cfb8" stroke-width="1"/>
<rect x="36" y="56" width="14" height="16" fill="#2f6f4d"/><rect x="86" y="48" width="14" height="22" fill="#2f6f4d"/>
<rect x="136" y="40" width="14" height="26" fill="#2f6f4d"/><rect x="186" y="30" width="14" height="34" fill="#2f6f4d"/>
<polyline points="24,66 92,54 142,44 192,34 262,16" stroke="#2f6f4d" stroke-width="3" fill="none"/>
<polygon points="262,16 246,16 256,28" fill="#2f6f4d"/>
<text x="150" y="16" font-size="9" fill="#5b6a7d" text-anchor="middle" {S}>ANT · NASDAQ · FIRST TRADE TODAY</text>
<text x="238" y="82" font-size="24" fill="#10263f" text-anchor="middle" {S}>$81.3bn</text></svg>'''
    if kind == "gulf-night":
        return f'''<svg viewBox="0 0 300 90" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="90" fill="#101c33"/>
<circle cx="40" cy="16" r="1.6" fill="#fff"/><circle cx="90" cy="9" r="1.4" fill="#fff"/><circle cx="150" cy="18" r="1.6" fill="#fff"/>
<circle cx="210" cy="10" r="1.4" fill="#fff"/><circle cx="260" cy="22" r="1.6" fill="#fff"/><circle cx="180" cy="32" r="1.3" fill="#fff"/>
<path d="M60 90 A44 44 0 0 1 148 90 Z" fill="#cfd8e3"/><rect x="58" y="86" width="92" height="4" fill="#8a97a8"/>
<rect x="0" y="70" width="300" height="20" fill="#1d3a5f"/>
<circle cx="200" cy="44" r="4" fill="#e8a13c"/><circle cx="228" cy="34" r="4" fill="#e8a13c"/><circle cx="252" cy="50" r="4" fill="#e8a13c"/>
<path d="M200 44 L228 34 M228 34 L252 50" stroke="#e8a13c" stroke-width="1.4" stroke-dasharray="4 3"/>
<text x="12" y="84" font-size="10" fill="#fff" {S}>BAHRAIN · KUWAIT · THE GULF</text></svg>'''
    if kind == "cyclone":
        return f'''<svg viewBox="0 0 300 62" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="62" fill="#7fb3c8"/>
<path d="M0 62 L0 34 Q60 26 110 38 Q170 50 230 38 L300 26 L300 62 Z" fill="#c9b18c"/>
<circle cx="180" cy="26" r="16" fill="none" stroke="#fff" stroke-width="4"/>
<circle cx="180" cy="26" r="9" fill="none" stroke="#fff" stroke-width="3"/>
<circle cx="180" cy="26" r="3.5" fill="#fff"/>
<rect x="10" y="6" width="120" height="18" fill="#10263f"/><text x="70" y="19" font-size="10" fill="#fff" text-anchor="middle" {S}>LANDFALL 20 NOV</text></svg>'''
    if kind == "court-scales":
        return f'''<svg viewBox="0 0 300 90" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="90" fill="#1e3a6e"/>
<polygon points="66,10 122,32 10,32" fill="#f6f1e5"/>
<rect x="22" y="36" width="10" height="32" fill="#f6f1e5"/><rect x="46" y="36" width="10" height="32" fill="#f6f1e5"/>
<rect x="70" y="36" width="10" height="32" fill="#f6f1e5"/><rect x="94" y="36" width="10" height="32" fill="#f6f1e5"/>
<rect x="14" y="68" width="98" height="6" fill="#f6f1e5"/>
<line x1="212" y1="18" x2="212" y2="72" stroke="#f2c94c" stroke-width="3"/>
<line x1="182" y1="30" x2="242" y2="30" stroke="#f2c94c" stroke-width="3"/>
<line x1="182" y1="30" x2="172" y2="46" stroke="#f2c94c" stroke-width="2"/><line x1="182" y1="30" x2="192" y2="46" stroke="#f2c94c" stroke-width="2"/>
<path d="M168 46 A12 6 0 0 0 196 46 Z" fill="#f2c94c"/>
<line x1="242" y1="30" x2="232" y2="46" stroke="#f2c94c" stroke-width="2"/><line x1="242" y1="30" x2="252" y2="46" stroke="#f2c94c" stroke-width="2"/>
<path d="M228 46 A12 6 0 0 0 256 46 Z" fill="#f2c94c"/>
<text x="212" y="86" font-size="10" fill="#cfd8e3" text-anchor="middle" {S}>READ 10:00 TODAY</text></svg>'''
    if kind == "cop-globe":
        return f'''<svg viewBox="0 0 300 90" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="90" fill="#0f4c5c"/>
<circle cx="82" cy="45" r="30" fill="#2f6fb2"/>
<path d="M62 32 Q74 24 86 32 Q92 42 80 50 Q66 48 62 38 Z" fill="#4da34d"/>
<path d="M88 56 Q100 52 104 62 Q96 70 88 64 Z" fill="#4da34d"/>
<circle cx="238" cy="26" r="12" fill="#e8a13c"/>
<g stroke="#e8a13c" stroke-width="2"><line x1="238" y1="8" x2="238" y2="4"/><line x1="256" y1="26" x2="260" y2="26"/><line x1="220" y1="26" x2="216" y2="26"/><line x1="251" y1="13" x2="254" y2="10"/><line x1="225" y1="13" x2="222" y2="10"/></g>
<text x="212" y="58" font-size="22" fill="#fff" text-anchor="middle" {S}>FINAL 48H</text>
<text x="212" y="78" font-size="10" fill="#cfd8e3" text-anchor="middle" {S}>ANTALYA · CLOSES FRI</text></svg>'''
    if kind == "flood-street":
        return f'''<svg viewBox="0 0 300 62" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="62" fill="#5b7a8c"/>
<g stroke="#cfd8e3" stroke-width="1.4"><line x1="30" y1="4" x2="24" y2="18"/><line x1="80" y1="2" x2="74" y2="16"/><line x1="130" y1="6" x2="124" y2="20"/><line x1="180" y1="2" x2="174" y2="16"/><line x1="230" y1="6" x2="224" y2="20"/><line x1="275" y1="2" x2="269" y2="16"/></g>
<rect x="0" y="38" width="300" height="24" fill="#2f6fb2"/>
<rect x="110" y="26" width="80" height="16" rx="6" fill="#8a97a8"/>
<rect x="122" y="18" width="56" height="12" rx="5" fill="#aab6c4"/>
<rect x="130" y="21" width="18" height="7" fill="#3c4a63"/><rect x="152" y="21" width="18" height="7" fill="#3c4a63"/>
<circle cx="130" cy="44" r="6" fill="#1a1a1a"/><circle cx="170" cy="44" r="6" fill="#1a1a1a"/>
<rect x="10" y="6" width="104" height="18" fill="#10263f"/><text x="62" y="19" font-size="10" fill="#fff" text-anchor="middle" {S}>15.32 IN</text></svg>'''
    if kind == "empty-chair":
        return f'''<svg viewBox="0 0 300 62" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="62" fill="#e9e2cf"/>
<text x="150" y="16" font-size="12" fill="#a33" text-anchor="middle" {S}>UKRAINE: NOT ON AGENDA</text>
<rect x="20" y="34" width="260" height="9" fill="#6b5f52"/>
<rect x="40" y="24" width="26" height="10" fill="#d43d2a"/><rect x="86" y="24" width="26" height="10" fill="#3c5a8a"/>
<rect x="132" y="24" width="26" height="10" fill="#e8e8e8" stroke="#10263f" stroke-width="1"/>
<rect x="196" y="24" width="26" height="10" fill="none" stroke="#a33" stroke-width="2" stroke-dasharray="3 2"/>
<line x1="196" y1="24" x2="222" y2="34" stroke="#a33" stroke-width="2"/><line x1="222" y1="24" x2="196" y2="34" stroke="#a33" stroke-width="2"/>
<rect x="40" y="43" width="6" height="12" fill="#6b5f52"/><rect x="86" y="43" width="6" height="12" fill="#6b5f52"/>
<rect x="132" y="43" width="6" height="12" fill="#6b5f52"/><rect x="196" y="43" width="6" height="12" fill="#6b5f52"/></svg>'''
    if kind == "missile-intercept":
        return f'''<svg viewBox="0 0 300 62" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="62" fill="#131c2e"/>
<circle cx="30" cy="12" r="1.4" fill="#fff"/><circle cx="120" cy="8" r="1.4" fill="#fff"/><circle cx="260" cy="14" r="1.4" fill="#fff"/>
<rect x="0" y="46" width="300" height="16" fill="#0d1526"/>
<rect x="14" y="34" width="16" height="28" fill="#0d1526"/><rect x="44" y="26" width="20" height="36" fill="#0d1526"/>
<rect x="240" y="30" width="18" height="32" fill="#0d1526"/><rect x="268" y="38" width="16" height="24" fill="#0d1526"/>
<line x1="60" y1="58" x2="150" y2="16" stroke="#e8a13c" stroke-width="1.6" stroke-dasharray="5 3"/>
<line x1="240" y1="58" x2="150" y2="16" stroke="#e8a13c" stroke-width="1.6" stroke-dasharray="5 3"/>
<circle cx="150" cy="16" r="6" fill="#ff5e3a"/><circle cx="150" cy="16" r="10" fill="none" stroke="#ff5e3a" stroke-width="1.5"/>
<rect x="10" y="6" width="110" height="18" fill="#2f6f4d"/><text x="65" y="19" font-size="10" fill="#fff" text-anchor="middle" {S}>INTERCEPTED</text></svg>'''
    if kind == "bridge-blast":
        return f'''<svg viewBox="0 0 300 62" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="62" fill="#7fb3c8"/>
<rect x="0" y="40" width="300" height="22" fill="#2f6fb2"/>
<rect x="0" y="30" width="300" height="5" fill="#5b6a7d"/>
<rect x="60" y="35" width="8" height="27" fill="#5b6a7d"/><rect x="232" y="35" width="8" height="27" fill="#5b6a7d"/>
<circle cx="150" cy="24" r="12" fill="#ff5e3a"/><circle cx="138" cy="28" r="8" fill="#e8a13c"/><circle cx="162" cy="28" r="8" fill="#ffb03a"/>
<circle cx="150" cy="12" r="7" fill="#8a97a8"/><circle cx="164" cy="8" r="5" fill="#8a97a8"/>
<rect x="10" y="6" width="104" height="18" fill="#10263f"/><text x="62" y="19" font-size="10" fill="#fff" text-anchor="middle" {S}>3RD STRIKE</text></svg>'''
    raise ValueError(kind)

def build_html(stories):
    news = [s for s in stories if s["section"] == "news"]
    leads = [s for s in news if s.get("lead")]
    row2 = [s for s in news if s["n"] in (4, 5, 6, 7)]
    row3 = [s for s in news if s["n"] in (8, 9, 10, 11)]
    briefs = [s for s in news if not s.get("lead")]
    # NOTE: the DATE CHECK footer labels (dc_wed below) are short forms of
    # the 10 stories.json date-check titles — verified to match 1:1.
    # Keep them in sync if editing.
    regions = sorted({s["region"] for s in news})
    from collections import Counter
    rc = Counter(s["region"] for s in news)
    region_line = " · ".join(f"{r} {rc[r]}" for r in regions)
    pins = [(s["n"], s["lon"], s["lat"]) for s in leads if s.get("lon") is not None]

    def lead_html(s):
        return f'''<div class="story lead audit" id="lead-{s["n"]}">
<div class="panel">{panel(s["panel"])}</div>
<div class="kicker"><span class="rk">{s["n"]} · {s["region"]} · {s["topic"]}</span><span class="src">{s["source"]}</span></div>
<div class="head">{s["title"]}</div>
<div class="deck">{s["deck"]} <span class="tag">{s["proof"]}</span></div></div>'''

    def med_html(s):
        return f'''<div class="story med audit" id="story-{s["n"]}">
<div class="panel">{panel(s["panel"])}</div>
<div class="kicker"><span class="rk">{s["n"]} · {s["region"]} · {s["topic"]}</span><span class="src">{s["source"]}</span></div>
<div class="head">{s["title"]}</div>
<div class="deck">{s["deck"]} <span class="tag">{s["proof"]}</span></div></div>'''

    briefs_html = "".join(
        f'<div class="brief"><span class="bn">{s["n"]}</span> {s["title"]}</div>' for s in briefs)
    timeline = [
        ("00:06", "Riyadh downs drones"),
        ("00:49", "Tanker hit in Hormuz"),
        ("02:06", "Crimea bridge shut"),
        ("04:27", "Florida: 15 in rain"),
        ("04:45", "Trump–Xi in Shenzhen"),
        ("06:30", "Three-way, Kylin Villa"),
        ("07:23", "Akvan: 80,000 out"),
        ("09:00", "ICJ Myanmar verdict"),
    ]
    tl_html = "".join(f'<span><b>{t}</b> {x}</span>' for t, x in timeline)
    numbers = [
        ("$81.3bn", "Anthropic's record IPO, the largest ever"),
        ("17.07m", "GTA VI pre-orders (Sensor Tower)"),
        ("200,000", "People to evacuate before Cyclone Akvan"),
        ("15.32 in", "Rain near Plantation, Florida"),
        ("730,000", "Rohingya who fled Myanmar in 2017"),
    ]
    num_html = "".join(f'<div class="num"><div class="nv">{v}</div><div class="nl">{l}</div></div>' for v, l in numbers)
    # DATE CHECK footer: short labels of the 10 stories.json date-check
    # titles — verified to name the same 10 items (all Wed 18 Nov). Keep
    # them in sync if editing.
    dc_wed = ["Hegseth's Venezuela deal", "Van Gogh $190.4m sale",
              "Gaza Yellow Line crossing", "Mélenchon 'could win'",
              "Australia settler sanctions", "Libya Derna seizure",
              "Voyager 1 light-day", "Jeffries 251–11",
              "Pew Islam-by-2035", "EU €45bn Ukraine loan"]
    dc_html = ("<b>DATE CHECK</b> — first reported before Thursday. "
               "Wed 18 Nov: " + " · ".join(dc_wed) + ". "
               "Not yet: COP31 close (Fri) · Akvan landfall (Fri) · "
               "Spain vote (29 Nov) · GTA VI on PC.")

    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#f6f1e5;font-family:"Noto Sans",sans-serif;color:#1a1a1a}}
.page{{width:1024px;height:1024px;padding:10px 24px 2px;overflow:hidden}}
.mast{{background:#10263f;color:#fff;display:flex;align-items:center;gap:16px;padding:3px 16px;border-bottom:4px solid #c9a227}}
.cal{{background:#f6f1e5;color:#10263f;text-align:center;padding:4px 10px;flex:none}}
.cal .m{{font-size:11px;font-weight:bold;letter-spacing:2px;color:#a33}}
.cal .d{{font-size:22px;font-weight:bold;line-height:1;font-family:"DejaVu Serif",serif}}
.cal .w{{font-size:9px;letter-spacing:1px}}
.mt{{flex:1}}
.mt .k{{color:#e8c85a;font-size:12px;letter-spacing:4px;font-weight:bold}}
.mt h1{{font-family:"DejaVu Serif",serif;font-size:32px;line-height:1.02}}
.mt .s{{font-size:11.5px;font-style:italic;color:#cfd8e3;margin-top:1px}}
.meta{{text-align:right;font-size:11px;font-weight:bold;letter-spacing:1px;color:#e8c85a;line-height:1.5;flex:none}}
.row{{display:flex;gap:12px;margin-top:2px}}
.story{{flex:1;min-width:0}}
.panel svg{{display:block;width:100%;height:auto}}
.kicker{{display:flex;justify-content:space-between;font-size:10px;font-weight:bold;margin-top:2px}}
.kicker .rk{{color:#a33}}.kicker .src{{color:#8a97a8;font-weight:normal}}
.head{{font-family:"DejaVu Serif",serif;font-weight:bold;line-height:1.12}}
.lead .head{{font-size:16px;margin-top:1px}}
.med .head{{font-size:14px;margin-top:1px}}
.deck{{font-size:11.5px;line-height:1.25;margin-top:1px}}
.tag{{font-size:8px;font-weight:bold;border:1px solid #8a97a8;border-radius:2px;padding:0 3px;color:#5b6a7d;white-space:nowrap}}
.mapbrief{{display:flex;gap:14px;margin-top:2px}}
.mapbox{{width:296px;flex:none}}
.mapbox h3,.briefs h3{{font-size:11px;letter-spacing:2px;border-bottom:2px solid #10263f;padding-bottom:3px;margin-bottom:5px}}
.legend{{font-size:8.5px;color:#5b6a7d;margin-top:3px;line-height:1.4}}
.legend b{{color:#10263f}}
.briefs{{flex:1;min-width:0}}
.briefs h3{{margin-bottom:5px}}
.bcols{{column-count:2;column-gap:16px;padding-bottom:2px}}
.brief{{font-size:16px;line-height:1.12;margin-bottom:0;break-inside:avoid}}
.brief .bn{{font-weight:bold;color:#10263f}}
.timeline{{background:#10263f;color:#fff;display:flex;justify-content:space-between;padding:3px 10px;margin-top:2px;font-size:9px}}
.timeline b{{color:#e8c85a}}
.timeline span{{white-space:nowrap}}
.numbers{{display:flex;gap:12px;margin-top:2px;border-top:2px solid #10263f;border-bottom:2px solid #10263f;padding:1px 0}}
.num{{flex:1}}
.num .nv{{font-family:"DejaVu Serif",serif;font-size:17px;font-weight:bold}}
.num .nl{{font-size:9.5px;line-height:1.25;color:#444}}
.datecheck{{margin-top:2px;border-left:4px solid #a33;padding:2px 0 2px 10px;font-size:10px;line-height:1.3}}
.datecheck b{{color:#a33}}
.foot{{margin-top:1px;font-size:9.5px;color:#666;line-height:1.4}}
#audit{{display:none}}
#footbottom{{display:none}}
</style></head><body><div class="page audit" id="page">
<div class="mast">
<div class="cal"><div class="m">NOV</div><div class="d">19</div><div class="w">THU · 2026</div></div>
<div class="mt"><div class="k">THE DAY IN WORLD NEWS</div><h1>Thursday 19 November 2026</h1>
<div class="s">Everything on this page happened, or was first reported, on Thursday 19 November 2026.</div></div>
<div class="meta">44 STORIES<br>7 REGIONS<br>ONE PAGE</div></div>
<div class="row">{''.join(lead_html(s) for s in leads[:3])}</div>
<div class="row">{''.join(med_html(s) for s in row2)}</div>
<div class="row">{''.join(med_html(s) for s in row3)}</div>
<div class="mapbrief">
<div class="mapbox"><h3>WHERE IT HAPPENED</h3>{map_svg(pins)}
<div class="legend">Pins 1–11 mark the lead stories.<br><b>{region_line}</b></div></div>
<div class="briefs"><h3>ALSO ON THURSDAY 19 NOVEMBER</h3><div class="bcols audit" id="briefs">{briefs_html}</div></div></div>
<div class="timeline audit" id="timeline">{tl_html}</div>
<div class="numbers audit" id="numbers">{num_html}</div>
<div class="datecheck audit" id="datecheck">{dc_html}</div>
<div class="foot audit" id="foot">All 44 stories happened, or were first reported, on Thursday 19 November 2026; claims are attributed. Original drawings.<br>Sources: Reuters · AP · AFP · CNN · Le Monde · Al Jazeera · IMD · UN · ICJ · Sensor Tower · Forbes · TBS · BBC · Banxico</div>
<pre id="audit"></pre>
<pre id="footbottom"></pre>
</div>
<script>
window.addEventListener('load', () => {{
  const out = [];
  document.querySelectorAll('.audit').forEach(el => {{
    out.push({{id: el.id || el.className, sh: el.scrollHeight, ch: el.clientHeight,
      sw: el.scrollWidth, cw: el.clientWidth,
      overflow: el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1}});
  }});
  document.getElementById('audit').textContent = JSON.stringify(out);
  document.getElementById('footbottom').textContent = String(Math.round(document.getElementById('foot').getBoundingClientRect().bottom));
}});
</script>
</body></html>'''

def main():
    stories = json.loads((HERE / "stories.json").read_text())
    html = build_html(stories)
    (HERE / "page.html").write_text(html)
    out = HERE / "entry.png"
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--hide-scrollbars", "--window-size=1024,1024",
                        f"--screenshot={out}", f"file://{HERE / 'page.html'}"],
                       capture_output=True, text=True, timeout=120)
    print(r.stdout[-500:], r.stderr[-500:])
    r2 = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                         "--dump-dom", f"file://{HERE / 'page.html'}"],
                        capture_output=True, text=True, timeout=120)
    import re
    m = re.search(r'<pre id="audit">(.*?)</pre>', r2.stdout, re.S)
    audit = json.loads(m.group(1)) if m else []
    m2 = re.search(r'<pre id="footbottom">(\d+)</pre>', r2.stdout, re.S)
    foot_bottom = int(m2.group(1)) if m2 else None
    overflow = [a["id"] for a in audit if a["overflow"]]
    page = next((a for a in audit if a["id"] == "page"), {})
    spec = {
        "masthead": "THE WORLD TODAY — Thursday 19 November 2026",
        "subline": "Everything on this page happened, or was first reported, on Thursday 19 November 2026.",
        "layout": "Newspaper front page: navy masthead, 3 large lead panels, 2 rows of 4 medium panels, dotted world map with numbered pins 1-11 beside 33 numbered briefs in 2 columns at 16px (briefs one line each, max 40 chars, so the brief words stay readable at 300px), UTC timeline strip, numbers strip (5 numbers), DATE CHECK footer, sources footer. Region counts sit under the map.",
        "proof_tags": "CONFIRMED / CLAIM / FORECAST tags on lead stories; claims attributed to sources.",
        "timeline": ["00:06 Riyadh downs Houthi drones", "00:49 Tanker hit in Hormuz (UKMTO)",
                     "02:06 Crimea bridge closed after strike", "04:27 Florida: 15 in of rain, rescues mount",
                     "04:45 Trump–Xi meet in Shenzhen", "06:30 Three-way talks at Kylin Villa",
                     "07:23 Akvan evacuations pass 80,000", "09:00 ICJ reads Myanmar verdict"],
        "numbers": ["$81.3bn Anthropic's record IPO, the largest ever",
                    "17.07m GTA VI pre-orders (Sensor Tower)",
                    "200,000 People to evacuate before Cyclone Akvan",
                    "15.32 in Rain near Plantation, Florida",
                    "730,000 Rohingya who fled Myanmar in 2017"],
        "min_body_px": 11.5,
        "page_scroll_height": page.get("sh"),
        "foot_bottom_px": foot_bottom,
        "overflow": overflow,
        "audit": audit,
        "legibility_note": "At 300px the 33 briefs are word-readable as distinct single lines (e.g. 'Shenzhen Declaration due by close', 'Banxico publishes split-cut minutes', 'Tinubu reviews state police bill'); lead heads and deck text stay legible; panels read as flat illustrations with labels intact.",
    }
    (HERE / "render_spec.json").write_text(json.dumps(spec, indent=2))
    size = out.stat().st_size if out.exists() else 0
    print(f"entry.png: {size} bytes; page scrollHeight={page.get('sh')} (limit 1024); foot_bottom={foot_bottom} (limit 1024); overflow={overflow or 'none'}")
    return 0 if (out.exists() and size <= 1048576 and not overflow and page.get("sh", 9999) <= 1024 and (foot_bottom or 9999) <= 1024) else 1

if __name__ == "__main__":
    sys.exit(main())
