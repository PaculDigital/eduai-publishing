#!/usr/bin/env python3
"""Cari kombinasi CSS yang: (a) animasi BERGERAK, (b) tetap menang
atas aturan OO, (c) teks tetap terbaca.

Dari diagnosa sebelumnya:
  - varian dgn `background:` shorthand + !important → animasi MATI
  - varian tanpa !important → animasi JALAN tapi kalah spesifisitas?
Uji di halaman yang MENIRU struktur + aturan OO.
"""
import time

from cloakbrowser import launch

# Tiruan aturan OO yang bikin putih (dari app.css OO)
OO_RULE = """
.toolbar .tabs li > a { color: #ffffff; }
.toolbar .tabs li.ribtab > a { color: #ffffff; font-weight: normal; }
"""

KANDIDAT = {
    # A: properti spesifik, TANPA !important pada background-*
    'A': """
.toolbar .tabs li.ribtab > a[data-title="AI"] {
    background-image: linear-gradient(90deg,
        #ffa000 15%, #ffd77a 35%, #fff3d0 50%, #ffd77a 65%, #ffa000 85%);
    background-size: 220% 100%;
    background-repeat: no-repeat;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: #ffa000;
    font-weight: 700;
    animation: eduaiAiShimmer 2.8s linear infinite;
}
""",
    # B: properti spesifik + !important HANYA di color/fill (bukan background)
    'B': """
.toolbar .tabs li.ribtab > a[data-title="AI"] {
    background-image: linear-gradient(90deg,
        #ffa000 15%, #ffd77a 35%, #fff3d0 50%, #ffd77a 65%, #ffa000 85%) !important;
    background-size: 220% 100% !important;
    background-repeat: no-repeat !important;
    -webkit-background-clip: text !important;
    background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    color: #ffa000 !important;
    font-weight: 700 !important;
    animation: eduaiAiShimmer 2.8s linear infinite !important;
}
""",
    # C: seperti B tapi keyframes pakai background-position-x
    'C': """
.toolbar .tabs li.ribtab > a[data-title="AI"] {
    background-image: linear-gradient(90deg,
        #ffa000 15%, #ffd77a 35%, #fff3d0 50%, #ffd77a 65%, #ffa000 85%) !important;
    background-size: 220% 100% !important;
    background-repeat: no-repeat !important;
    -webkit-background-clip: text !important;
    background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    color: #ffa000 !important;
    font-weight: 700 !important;
    animation: eduaiAiShimmerX 2.8s linear infinite !important;
}
""",
    # D: background-image TANPA !important (animasi pasti jalan),
    #    tapi color/fill pakai !important (menang atas aturan OO)
    'D': """
.toolbar .tabs li.ribtab > a[data-title="AI"] {
    background-image: linear-gradient(90deg,
        #ffa000 15%, #ffd77a 35%, #fff3d0 50%, #ffd77a 65%, #ffa000 85%);
    background-size: 220% 100%;
    background-repeat: no-repeat;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent !important;
    color: #ffa000 !important;
    font-weight: 700 !important;
    animation: eduaiAiShimmer 2.8s linear infinite;
}
""",
}


def bikin_html(kunci):
    return f"""<!DOCTYPE html><html><head><style>
body {{ background:#446995; margin:0; padding:20px;
        font-family:sans-serif; font-size:28px; }}
{OO_RULE}
@keyframes eduaiAiShimmer {{
    0%   {{ background-position: -220% 0; }}
    100% {{ background-position: 220% 0; }}
}}
@keyframes eduaiAiShimmerX {{
    0%   {{ background-position-x: -220%; }}
    100% {{ background-position-x: 220%; }}
}}
{KANDIDAT[kunci]}
</style></head><body>
<div class="toolbar">
<ul class="tabs" style="list-style:none;padding:0">
  <li class="ribtab"><a data-title="Home">Halaman Depan</a></li>
  <li class="ribtab"><a data-title="AI">AI</a></li>
</ul>
</div>
</body></html>"""


BACA = """()=>{
    const a=document.querySelector('a[data-title="AI"]');
    const home=document.querySelector('a[data-title="Home"]');
    const c=getComputedStyle(a), ch=getComputedStyle(home);
    return {pos:c.backgroundPosition, posx:c.backgroundPositionX,
            anim:c.animationName, state:c.animationPlayState,
            fill:c.webkitTextFillColor, clip:(c.webkitBackgroundClip||c.backgroundClip),
            color:c.color, weight:c.fontWeight, bgimg:c.backgroundImage.slice(0,40),
            home_warna: ch.color, home_weight: ch.fontWeight};}"""

b = launch(headless=True)
page = b.new_page()
for kunci in ['A', 'B', 'C', 'D']:
    open('/tmp/k.html', 'w').write(bikin_html(kunci))
    page.goto('file:///tmp/k.html', wait_until='domcontentloaded')
    time.sleep(0.6)
    r1 = page.evaluate(BACA)
    time.sleep(1.5)
    r2 = page.evaluate(BACA)
    gerak = (r1['pos'] != r2['pos']) or (r1['posx'] != r2['posx'])
    print(f"=== KANDIDAT {kunci} ===", flush=True)
    print(f"  background-position : {r1['pos']}  →  {r2['pos']}", flush=True)
    print(f"  animasi             : {r1['anim']} ({r1['state']})", flush=True)
    print(f"  clip / fill         : {r1['clip']} / {r1['fill']}", flush=True)
    print(f"  warna tab AI        : {r1['color']} (weight {r1['weight']})",
          flush=True)
    print(f"  warna tab HOME(kontrol): {r1['home_warna']}", flush=True)
    print(f"  → {'✅ BERGERAK' if gerak else '❌ STATIS'}", flush=True)
    print(flush=True)
    page.screenshot(path=f'shots/kand_{kunci}.png')
b.close()
