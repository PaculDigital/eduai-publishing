#!/usr/bin/env python3
"""Uji VISUAL: apakah bar biru editor sekarang menampilkan logo EduAi INOVASI?

Ambil screenshot area header editor (crop bagian atas).
"""
import json
import subprocess
import sys
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


browser = launch(headless=True)
ctx = browser.new_context()
page = ctx.new_page()
page.set_viewport_size({'width': 1440, 'height': 900})

print("=" * 76)
print("UJI VISUAL LOGO HEADER EDITOR")
print("=" * 76)

page.goto(f'{BASE}/masuk', wait_until='domcontentloaded', timeout=60000)
page.wait_for_timeout(2500)
page.fill('input[name="email"]', EMAIL)
page.fill('input[name="password"]', SANDI)
page.click('button[type="submit"]')
page.wait_for_timeout(5000)

fid = sq("SELECT id FROM files WHERE user_id=15 ORDER BY id DESC LIMIT 1")
page.goto(f'{BASE}/edit/{fid[0][0]}', wait_until='domcontentloaded',
          timeout=90000)

fr = None
for d in range(90):
    page.wait_for_timeout(2000)
    for x in page.frames[1:]:
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
        print(f"[editor siap] ~{(d+1)*2}s")
        break

if fr is None:
    print("❌ editor tidak siap")
    page.screenshot(path=str(SHOT / 'logo-header-cek-gagal.png'))
    sys.exit(1)

page.wait_for_timeout(4000)

f1 = SHOT / 'logo-header-01-full.png'
page.screenshot(path=str(f1))
print(f"📸 {f1}")

# ── cek elemen #header-logo ──
hasil = fr.evaluate("""() => {
    const el = document.querySelector('#header-logo');
    if (!el) return {ada: false};
    const img = el.querySelector('img');
    const bg = getComputedStyle(el).backgroundImage;
    const r = el.getBoundingClientRect();
    return {
        ada: true,
        hidden: el.classList.contains('hidden'),
        lebar: Math.round(r.width),
        tinggi: Math.round(r.height),
        adaImg: !!img,
        srcImg: img ? (img.src || '').slice(0, 80) : null,
        background: bg.slice(0, 120),
        teks: (el.innerText || '').trim()
    };
}""")
print(f"\n[#header-logo] {json.dumps(hasil, indent=1)}")

# crop area header atas (0-70px)
try:
    hdr = fr.locator('#header-logo')
    if hdr.count():
        f2 = SHOT / 'logo-header-02-crop.png'
        # ambil area sekitar logo
        fr.evaluate("""() => {
            const el = document.querySelector('#header-logo');
            return el ? 'ok' : 'no';
        }""")
        page.screenshot(path=str(f2), clip={'x': 0, 'y': 0, 'width': 500,
                                            'height': 60})
        print(f"📸 crop header: {f2}")
except Exception as e:
    print(f"crop: {e}")

browser.close()
