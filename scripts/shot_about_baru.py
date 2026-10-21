#!/usr/bin/env python3
"""Screenshot ABOUT setelah rebranding — bukti hasil perubahan.

Bandingkan isi dialog: harus menampilkan 'EduAi INOVASI', alamat Bekasi,
eduai@bikinaja.id, +6281-000-000, eduai.bikinaja.id — BUKAN Ascensio/Latvia.
"""
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


browser = launch(headless=True)
page = browser.new_page()
page.set_viewport_size({'width': 1440, 'height': 900})

print("=" * 74)
print("SCREENSHOT ABOUT SETELAH REBRANDING")
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
for detik in range(60):
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
        print(f"[editor siap] ~{(detik+1)*2}s")
        break

if fr is None:
    print("❌ editor tidak siap")
    page.screenshot(path=str(SHOT / 'about-baru-gagal.png'))
    browser.close()
    raise SystemExit(1)

page.wait_for_timeout(3000)
fr.locator('#left-btn-about').click(timeout=15000)
page.wait_for_timeout(5000)

f1 = SHOT / 'about-baru-01.png'
page.screenshot(path=str(f1))
print(f"📸 {f1}")

isi = fr.evaluate("""() => {
    const t = document.body.innerText || '';
    return {
        adaEduAi: /EduAi INOVASI/i.test(t),
        adaBekasi: /Bekasi/i.test(t),
        adaEmailBaru: /eduai@bikinaja\\.id/i.test(t),
        adaTelpBaru: /6281/i.test(t),
        adaWebsiteBaru: /eduai\\.bikinaja\\.id/i.test(t),
        masihAscensio: /ascensio/i.test(t),
        masihLatvia: /latvia/i.test(t),
        masihSupportOO: /support@onlyoffice/i.test(t),
        potongan: t.replace(/\\s+/g,' ').slice(0, 500)
    };
}""")
print(f"\n[ISI DIALOG] {json.dumps(isi, indent=1, ensure_ascii=False)}")

# screenshot kotak dialog saja
try:
    dlg = fr.locator('#id-about-licensor-info')
    if dlg.count() and dlg.first.is_visible():
        f2 = SHOT / 'about-baru-zoom.png'
        dlg.first.screenshot(path=str(f2))
        print(f"📸 zoom dialog: {f2}")
except Exception as e:
    print(f"zoom gagal: {e}")

browser.close()
print("\nSELESAI.")
