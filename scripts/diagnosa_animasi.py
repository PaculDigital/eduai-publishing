#!/usr/bin/env python3
"""Diagnosa: kenapa background-position tidak bergerak walau animationName aktif?

Hipotesis (harus diuji satu-satu, JANGAN diklaim tanpa bukti):
  H1. Animasi berjalan TAPI background-clip:text membuat posisi tak terlihat
  H2. Animasi benar-benar TIDAK berjalan (mis. elemen punya `display:none`
      di momen tertentu, atau animation-play-state: paused dari OO)
  H3. Aturan OO lain mematikan animasi lewat `animation: none` di rule
      yang lebih spesifik

Uji terisolasi: bikin elemen tiruan dengan CSS yang SAMA PERSIS, lihat apakah
background-position bergerak di browser ini. Kalau bergerak → masalahnya di
OO/timing. Kalau tidak → masalahnya di CSS/sintaks.
"""
import sys
import time

from cloakbrowser import launch

HTML = """<!DOCTYPE html><html><head><style>
body { background:#446995; margin:0; padding:20px; font-family:sans-serif; }
@keyframes eduaiAiShimmer {
    0%   { background-position: -220% 0; }
    100% { background-position: 220% 0; }
}
/* VARIAN 1: persis seperti di app.css */
.v1 {
    background: linear-gradient(90deg,
        #ffa000 15%, #ffd77a 35%, #fff3d0 50%, #ffd77a 65%, #ffa000 85%) !important;
    background-size: 220% 100% !important;
    -webkit-background-clip: text !important;
    background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    color: #ffa000 !important;
    font-weight: 700 !important;
    animation: eduaiAiShimmer 2.8s linear infinite !important;
}
/* VARIAN 2: tanpa background-clip:text (gradien di latar elemen) */
.v2 {
    background: linear-gradient(90deg,
        #ffa000 15%, #ffd77a 35%, #fff3d0 50%, #ffd77a 65%, #ffa000 85%);
    background-size: 220% 100%;
    color: #fff;
    animation: eduaiAiShimmer 2.8s linear infinite;
}
/* VARIAN 3: tanpa !important */
.v3 {
    background: linear-gradient(90deg,
        #ffa000 15%, #ffd77a 35%, #fff3d0 50%, #ffd77a 65%, #ffa000 85%);
    background-size: 220% 100%;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: eduaiAiShimmer 2.8s linear infinite;
}
/* VARIAN 4: keyframes pakai background-position-x saja */
@keyframes eduaiAiShimmerX {
    0%   { background-position-x: -220%; }
    100% { background-position-x: 220%; }
}
.v4 {
    background: linear-gradient(90deg,
        #ffa000 15%, #ffd77a 35%, #fff3d0 50%, #ffd77a 65%, #ffa000 85%);
    background-size: 220% 100%;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: eduaiAiShimmerX 2.8s linear infinite;
}
</style></head><body>
<div id="a" class="v1" style="font-size:28px">AI v1</div>
<div id="b" class="v2" style="font-size:28px">AI v2</div>
<div id="c" class="v3" style="font-size:28px">AI v3</div>
<div id="d" class="v4" style="font-size:28px">AI v4</div>
</body></html>"""

BACA = """()=>{
    const out={};
    for (const id of ['a','b','c','d']) {
        const el=document.getElementById(id);
        const c=getComputedStyle(el);
        out[id]={anim:c.animationName, dur:c.animationDuration,
                 state:c.animationPlayState, pos:c.backgroundPosition,
                 posx:c.backgroundPositionX, clip:(c.webkitBackgroundClip||c.backgroundClip),
                 size:c.backgroundSize};
    }
    // apakah animasi benar-benar ada?
    out.animasi = [...document.getAnimations()].map(a=>({
        name:a.animationName||'', state:a.playState,
        cur:(a.currentTime||0).toFixed(0)}));
    return out;}"""

b = launch(headless=True)
page = b.new_page()
open("/tmp/iso.html","w").write(HTML)
page.goto("file:///tmp/iso.html", wait_until="domcontentloaded")
time.sleep(0.6)

print('=== PUTARAN 1 ===', flush=True)
r1 = page.evaluate(BACA)
for k in ['a', 'b', 'c', 'd']:
    print(f"  {k}: pos={r1[k]['pos']:12} posx={str(r1[k]['posx']):10} "
          f"anim={r1[k]['anim']:20} state={r1[k]['state']}", flush=True)
print('  animasi terdaftar:', r1['animasi'], flush=True)

time.sleep(1.5)
print('\n=== PUTARAN 2 (jeda 1,5s) ===', flush=True)
r2 = page.evaluate(BACA)
for k in ['a', 'b', 'c', 'd']:
    s = 'BERGERAK ✅' if r1[k]['pos'] != r2[k]['pos'] or r1[k]['posx'] != r2[k]['posx'] else 'statis ❌'
    print(f"  {k}: pos={r2[k]['pos']:12} → {s}", flush=True)
print('  animasi:', r2['animasi'], flush=True)

# bukti piksel: screenshot berturut
page.screenshot(path='shots/iso_1.png')
time.sleep(1.0)
page.screenshot(path='shots/iso_2.png')
b.close()
print('\nscreenshot: shots/iso_1.png, shots/iso_2.png', flush=True)
