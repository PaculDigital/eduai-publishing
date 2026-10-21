#!/usr/bin/env python3
"""UJI VISUAL TAHAP 1: buka EDITOR di browser nyata, rekam judul tab.

Membuktikan perubahan TERLIHAT oleh user, bukan cuma benar di sisi server.
Juga screenshot untuk bukti.

Jalankan: /opt/data/services/cloakbrowser/.venv/bin/python3 scripts/uji_visual_tahap1.py
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
SHOT.mkdir(exist_ok=True)


def sq(sql):
    out = subprocess.run(
        ['docker', 'exec', CONTAINER, 'python3', '-c',
         f"import sqlite3,json;c=sqlite3.connect('{DB}');"
         f"print(json.dumps(c.execute({sql!r}).fetchall()))"],
        capture_output=True, text=True, timeout=60)
    return json.loads(out.stdout.strip() or '[]')


print("=" * 76)
print("UJI VISUAL TAHAP 1 — JUDUL TAB DI EDITOR (browser nyata)")
print("=" * 76)

browser = launch(headless=True)
page = browser.new_page()
page.set_viewport_size({'width': 390, 'height': 844})

# ── 1. halaman login ─────────────────────────────────────────────
page.goto(f'{BASE}/masuk', wait_until='domcontentloaded', timeout=60000)
page.wait_for_timeout(2500)
t1 = page.title()
print(f"\n[login]    judul tab: '{t1}'")

# ── 2. login ─────────────────────────────────────────────────────
page.fill('input[name="email"]', EMAIL)
page.fill('input[name="password"]', SANDI)
page.click('button[type="submit"]')
page.wait_for_timeout(4500)
t2 = page.title()
print(f"[setelah login] judul tab: '{t2}'")
print(f"    URL: {page.url}")

# ── 3. buka file pertama ─────────────────────────────────────────
berkas = sq("SELECT id, judul FROM files LIMIT 1")
print(f"\n[berkas] dari DB: {berkas}")
if berkas:
    fid = berkas[0][0]
    page.goto(f'{BASE}/edit/{fid}', wait_until='domcontentloaded',
              timeout=90000)
    # tunggu editor render
    for i in range(20):
        page.wait_for_timeout(2000)
        t3 = page.title()
        iframe = page.query_selector('iframe')
        if iframe or 'editor' in t3.lower():
            break
    t3 = page.title()
    print(f"\n[editor]   judul tab: '{t3}'")
    print(f"    ada iframe editor: {page.query_selector('iframe') is not None}")

    # cek judul di dalam iframe juga
    for fr in page.frames[1:]:
        try:
            judul_if = fr.evaluate('document.title')
            if judul_if:
                print(f"    judul iframe: '{judul_if}'")
        except Exception:
            pass

    cek = 'ONLYOFFICE' in t3.upper()
    print(f"\n    masih 'ONLYOFFICE'? {'YA ❌' if cek else 'TIDAK ✅'}")

    f = SHOT / 'rebrand-tahap1-editor.png'
    page.screenshot(path=str(f))
    print(f"📸 screenshot: {f}")

# ── 4. favicon di beranda ────────────────────────────────────────
page.goto(f'{BASE}/', wait_until='domcontentloaded', timeout=60000)
page.wait_for_timeout(2000)
info = page.evaluate("""() => {
    const o = [];
    document.querySelectorAll('link[rel*="icon"]').forEach(l =>
        o.push({rel: l.rel, href: l.href}));
    return o;
}""")
print(f"\n[favicon beranda] {json.dumps(info, indent=2)}")

page.screenshot(path=str(SHOT / 'rebrand-tahap1-beranda.png'))
print(f"📸 screenshot: {SHOT / 'rebrand-tahap1-beranda.png'}")

browser.close()
print("\nSELESAI.")
