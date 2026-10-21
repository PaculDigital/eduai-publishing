#!/usr/bin/env python3
"""Ambil screenshot DETAIL header biru OnlyOffice (area atas editor)."""
import json
import subprocess
from pathlib import Path

from cloakbrowser import launch

BASE = 'https://eduai.bikinaja.id'
EMAIL = 'uji.lengkap@eduai.local'
SANDI = 'ujiLengkap12345'
CONTAINER = 'eduai-app'
DB = '/app/data/eduai.db'
SHOT = Path('/opt/data/services/eduai-publishing/shots')


def sq(sql):
    out = subprocess.run(
        ['docker', 'exec', CONTAINER, 'python3', '-c',
         f"import sqlite3,json;c=sqlite3.connect('{DB}');"
         f"print(json.dumps(c.execute({sql!r}).fetchall()))"],
        capture_output=True, text=True, timeout=60)
    return json.loads(out.stdout.strip() or '[]')


b = launch(headless=True)
ctx = b.new_context()
p = ctx.new_page()
p.set_viewport_size({'width': 1440, 'height': 900})

p.goto(f'{BASE}/masuk', wait_until='domcontentloaded', timeout=60000)
p.wait_for_timeout(2500)
p.fill('input[name="email"]', EMAIL)
p.fill('input[name="password"]', SANDI)
p.click('button[type="submit"]')
p.wait_for_timeout(5000)

fid = sq("SELECT id FROM files WHERE user_id=15 ORDER BY id DESC LIMIT 1")
p.goto(f'{BASE}/edit/{fid[0][0]}', wait_until='domcontentloaded', timeout=90000)

fr = None
for d in range(90):
    p.wait_for_timeout(2000)
    for x in p.frames[1:]:
        try:
            if x.evaluate("""() => {
                const b = document.querySelector('#left-btn-about');
                if (!b) return false;
                const r = b.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            }"""):
                fr = x
                break
        except Exception:
            pass
    if fr:
        print(f"[siap] ~{(d+1)*2}s")
        break

p.wait_for_timeout(5000)

# ── cari posisi iframe OO & header biru di dalamnya ──
info = p.evaluate("""() => {
    const f = document.querySelector('iframe');
    if (!f) return null;
    const r = f.getBoundingClientRect();
    return {x: Math.round(r.x), y: Math.round(r.y),
            w: Math.round(r.width), h: Math.round(r.height)};
}""")
print(f"[iframe] {json.dumps(info)}")

# ambil posisi header OO di dalam iframe
pos = None
if fr:
    pos = fr.evaluate("""() => {
        // header biru OO: elemen paling atas, cari .toolbar-header atau #header-logo
        const kandidat = ['#header-logo', '.toolbar-header',
                          '#viewport-toolbar', '.toolbar'];
        const hasil = [];
        kandidat.forEach(sel => {
            const e = document.querySelector(sel);
            if (e) {
                const r = e.getBoundingClientRect();
                hasil.push({sel, x: Math.round(r.x), y: Math.round(r.y),
                            w: Math.round(r.width), h: Math.round(r.height)});
            }
        });
        return hasil;
    }""")
print(f"[elemen header OO] {json.dumps(pos, indent=1)}")

# screenshot penuh
f1 = SHOT / 'header-biru-01-full.png'
p.screenshot(path=str(f1))
print(f"📸 {f1}")

# crop area header biru (biasanya di bawah header hijau, ~60-120px)
if info:
    f2 = SHOT / 'header-biru-02-crop.png'
    p.screenshot(path=str(f2), clip={'x': info['x'], 'y': info['y'],
                                     'width': info['w'], 'height': 120})
    print(f"📸 {f2}")

b.close()
