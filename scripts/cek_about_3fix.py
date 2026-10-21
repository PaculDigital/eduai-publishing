#!/usr/bin/env python3
"""Cek URL yang BENAR-BENAR tampil di About + lihat SEMUA teks persisnya."""
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
        break

if fr is None:
    print("❌ editor tidak siap")
    sys.exit(1)

page.wait_for_timeout(2500)
fr.locator('#left-btn-about').click(timeout=15000)
page.wait_for_timeout(4000)

f1 = SHOT / 'about-3fix-01.png'
page.screenshot(path=str(f1))
print(f"📸 {f1}")

# ── baca SELURUH teks + href persis ──
hasil = fr.evaluate("""() => {
    const t = document.body.innerText || '';
    // ambil elemen url & mail khusus
    const url = document.querySelector('#id-about-company-url, '
                  + '.asc-about-companyname ~ * a');
    const semuaLink = [];
    document.querySelectorAll('a').forEach(a => {
        const x = (a.innerText || '').trim();
        if (x && (x.includes('.') || x.includes('@'))) {
            semuaLink.push({teks: x, href: a.getAttribute('href')});
        }
    });
    return {
        teksPenuh: t.replace(/\\s+/g,' '),
        link: semuaLink,
        masihSurel: /surel/i.test(t),
        adaWww: /www\\./i.test(t),
        adaEmailLabel: /email:/i.test(t)
    };
}""")
print(f"\n[LINK & TEKS]")
print(json.dumps(hasil, indent=1, ensure_ascii=False))

# zoom bagian licensor
try:
    dlg = fr.locator('#id-about-licensor-info')
    if dlg.count() and dlg.first.is_visible():
        f2 = SHOT / 'about-3fix-zoom.png'
        dlg.first.screenshot(path=str(f2))
        print(f"\n📸 zoom: {f2}")
except Exception as e:
    print(f"zoom: {e}")

browser.close()
