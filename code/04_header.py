"""Step 4. Make header.png (1200x630 social card) by rendering a small HTML card with Playwright.

Run after 03_build_page.py (it reads the data embedded in index.html).

Usage:
    python3 code/04_header.py [--fontsource DIR]

Fonts come from Google Fonts. Where Google Fonts is unreachable, pass --fontsource with a folder
holding unpacked npm packages @fontsource/fraunces, @fontsource/source-serif-4 and
@fontsource/ibm-plex-mono (folders named fontsource-<name>-<version>/package/...).
"""
import asyncio
import glob
import json
import math
import os
import re
import sys

from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
S = json.loads(re.search(r"const D = (\{.*?\});\nconst R", open(os.path.join(ROOT, "index.html"), encoding="utf-8").read(), re.S).group(1))
FONTSRC = sys.argv[sys.argv.index("--fontsource") + 1] if "--fontsource" in sys.argv else None

# places: [lat, lng, households, growth class]
pts = []
for a in S["places"]:
    par = S["parishes"][a[11]] if a[11] >= 0 else None
    r = par[5] if par else None
    g = -1 if r is None else (0 if r < 1 else 1 if r < 3 else 2 if r < 10 else 3 if r < 30 else 4 if r < 100 else 5)
    pts.append([a[0], a[1], a[4] or 0, g])
pts.sort(key=lambda p: -p[2])

HTML = """<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,900&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:opsz,wght@8..60,400&display=swap">
<style>
body{margin:0;width:1200px;height:630px;background:#15140F;color:#EDE8DC;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}
.l{position:absolute;left:72px;top:64px;width:640px}
.k{font:500 17px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#A59E8E;display:flex;gap:14px;align-items:center}
.k b{background:#F26A30;color:#15140F;padding:8px 10px;font-weight:500}
h1{font:900 104px/.88 'Fraunces',Georgia,serif;letter-spacing:-.02em;margin:26px 0 0}
h1 em{font-style:normal;color:#F26A30}
p{font-size:27px;line-height:1.36;margin:24px 0 0;color:#D9D3C5;max-width:560px}
.f{position:absolute;left:72px;bottom:36px;font:400 15px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#8C8577}
canvas{position:absolute;right:30px;top:20px}
</style></head><body>
<div class="l"><div class="k"><b>Data study</b><span>History × data</span></div>
<h1>Is <em>Domesday</em> destiny?</h1>
<p>__DEK__</p></div>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<canvas id="c" width="1060" height="1180" style="width:530px;height:590px"></canvas>
<script>
const P = __PTS__;
const C = ["#FF6A3D","#E88A55","#B98A68","#6E93B5","#5A9BE0","#8CC4FF"], N = "#5A5549";
const cv = document.getElementById("c"), x = cv.getContext("2d"); x.scale(2, 2);
const lat0 = 52.6, k = Math.cos(lat0 * Math.PI / 180), lo0 = -5.8, lo1 = 1.9, la0 = 49.9, la1 = 55.85;
const sc = Math.min(530 / ((lo1 - lo0) * k), 590 / (la1 - la0));
const X = l => (l - lo0) * k * sc + (530 - (lo1 - lo0) * k * sc) / 2, Y = l => (la1 - l) * sc;
for (const p of P) { const r = p[2] > 0 ? 0.6 + Math.sqrt(p[2]) * 0.3 : 0.6; x.beginPath(); x.arc(X(p[1]), Y(p[0]), r, 0, 6.2832);
  x.fillStyle = p[3] < 0 ? N : C[p[3]]; x.globalAlpha = 0.85; x.fill(); }
</script></body></html>"""
dek = (f"{R['places_located']:,} places from 1086 against the 2021 census. "
       "Size then barely predicts size now.")
html = HTML.replace("__PTS__", json.dumps(pts, separators=(",", ":"))).replace("__DEK__", dek)
tmp = os.path.join(ROOT, "_header_tmp.html")
open(tmp, "w", encoding="utf-8").write(html)


def fontcss():
    css = ""
    for fam, name, ws in [("Fraunces", "fraunces", [900]), ("Source Serif 4", "source-serif-4", [400]),
                          ("IBM Plex Mono", "ibm-plex-mono", [400, 500])]:
        d = glob.glob(os.path.join(FONTSRC, f"fontsource-{name}-*"))[0]
        for w in ws:
            css += (f"@font-face{{font-family:'{fam}';font-weight:{w};src:url(file://{d}/package/files/"
                    f"{name}-latin-{w}-normal.woff2) format('woff2')}}\n")
    return css


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1200, "height": 630})
        if FONTSRC:
            css = fontcss()

            async def route(r):
                if "fonts.googleapis.com" in r.request.url:
                    return await r.fulfill(body=css, content_type="text/css")
                return await r.continue_()
            await pg.route("**/*", route)
        await pg.goto("file://" + tmp)
        await pg.wait_for_timeout(1200)
        await pg.screenshot(path=os.path.join(ROOT, "header.png"))
        await b.close()

asyncio.run(main())
os.remove(tmp)
print("header.png written")
