#!/usr/bin/env python3
"""Uji About SETELAH rebranding — dengan CACHE BERSIH (konteks browser baru).

Pelajaran: browser menyimpan About.js lama di cache. Harus:
  - konteks browser BARU (tidak reuse)
  - hard reload (bypass cache)
  - tambah query anti-cache

Hasil harus menampilkan EduAi INOVASI, bukan Ascensio.
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
# konteks baru = cache kosong
ctx = browser.new_context(bypass_csp=True)
page = ctx.new_page()
page.set_viewport_size({'width': 1440, 'height': 900})

print("=" * 74)
print("UJI ABOUT DENGAN CACHE BERSIH")
print("=" * 74)

page.goto(f'{BASE}/masuk', wait_until='domcontentloaded', timeout=60000)
page.wait_for_timeout(2500)
page.fill('input[name="email"]', EMAIL)
page.fill('input[name="password"]', SANDI)
page.click('button[type="submit"]')
page.wait_for_timeout(5000)

fid = sq("SELECT id FROM files WHERE user_id=15 ORDER BY id DESC LIMIT 1")
idf = fid[0][0]
page.goto(f'{BASE}/edit/{idf}', wait_until='domcontentloaded', timeout=90000)

fr = None
for d in range(60):
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
    page.screenshot(path=str(SHOT / 'about-cek-gagal.png'))
    sys.exit(1)

page.wait_for_timeout(3000)

# tunggu tombol About benar-benar AKTIF (bukan disabled)
aktif = False
for t in range(45):
    try:
        st = fr.evaluate(
            "() => { const b = document.querySelector('#left-btn-about');"
            " return b ? !b.disabled : false; }")
        if st:
            aktif = True
            print(f"[tombol About aktif] ~{t}s")
            break
    except Exception:
        pass
    page.wait_for_timeout(1000)
if not aktif:
    print("⚠️ tombol About masih disabled -> klik paksa")

fr.evaluate("""() => {
    const b = document.querySelector('#left-btn-about');
    if (!b) return 'tidak-ada';
    b.disabled = false;
    b.classList.remove('disabled');
    b.dispatchEvent(new MouseEvent('click', {bubbles: true}));
    return 'diklik';
}""")
page.wait_for_timeout(5000)

f1 = SHOT / 'about-FINAL-01.png'
page.screenshot(path=str(f1))
print(f"📸 {f1}")

isi = fr.evaluate("""() => {
    const t = document.body.innerText || '';
    return {
        adaEduAi: /EduAi INOVASI/i.test(t),
        adaBekasi: /Bekasi/i.test(t),
        adaEmailBaru: /eduai@bikinaja\\.id/i.test(t),
        adaTelpBaru: /6281/i.test(t),
        adaWebBaru: /eduai\\.bikinaja\\.id/i.test(t),
        masihAscensio: /ascensio/i.test(t),
        masihLatvia: /latvia/i.test(t),
        potongan: t.replace(/\\s+/g,' ').slice(0, 420)
    };
}""")
print(f"\n[ISI DIALOG] {json.dumps(isi, indent=1, ensure_ascii=False)}")

# zoom dialog
try:
    dlg = fr.locator('#id-about-licensor-info')
    if dlg.count() and dlg.first.is_visible():
        f2 = SHOT / 'about-FINAL-zoom.png'
        dlg.first.screenshot(path=str(f2))
        print(f"📸 zoom: {f2}")
except Exception as e:
    print(f"zoom: {e}")

browser.close()
print("\nSELESAI.")
