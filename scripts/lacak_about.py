#!/usr/bin/env python3
"""LACAK: file About.js MANA yang benar-benar DIMUAT browser?

Rekam SEMUA request .js dari editor, lalu periksa isi About.js yang diunduh.
Ini akan menunjukkan sumber sebenarnya (mungkin ada bundel / file lain).
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

dari_iframe = []
page.on('response', lambda r: dari_iframe.append(r.url)
        if '.js' in r.url else None)

page.goto(f'{BASE}/masuk', wait_until='domcontentloaded', timeout=60000)
page.wait_for_timeout(2500)
page.fill('input[name="email"]', EMAIL)
page.fill('input[name="password"]', SANDI)
page.click('button[type="submit"]')
page.wait_for_timeout(5000)

fid = sq("SELECT id FROM files WHERE user_id=15 ORDER BY id DESC LIMIT 1")
page.goto(f'{BASE}/edit/{fid[0][0]}', wait_until='domcontentloaded',
          timeout=90000)
for d in range(40):
    page.wait_for_timeout(2000)
    if page.query_selector('iframe'):
        break
page.wait_for_timeout(8000)

print("=" * 76)
print("1. SEMUA REQUEST .js YANG MENYEBUT 'About'")
print("=" * 76)
about_urls = [u for u in dari_iframe if 'About' in u or 'about' in u]
for u in sorted(set(about_urls)):
    print(f"  {u}")
if not about_urls:
    print("  (tidak ada — mungkin termuat dari cache)")

print(f"\n  total request .js direkam: {len(dari_iframe)}")
print("\n  contoh 12 request pertama:")
for u in dari_iframe[:12]:
    print(f"    {u[:110]}")

print("\n" + "=" * 76)
print("2. CARI DI DALAM SEMUA FRAME: teks 'Ascensio' ada di JS mana?")
print("=" * 76)
for i, fr in enumerate(page.frames):
    try:
        hasil = fr.evaluate("""() => {
            // cari apakah ada variabel/config yg memuat Ascensio
            const t = document.documentElement.innerHTML || '';
            return {
                url: location.href.slice(0, 90),
                adaAscensio: /Ascensio/.test(t),
                adaEduAi: /EduAi INOVASI/.test(t)
            };
        }""")
        if hasil.get('adaAscensio') or hasil.get('adaEduAi'):
            print(f"  frame[{i}] {hasil}")
    except Exception:
        pass

print("\n" + "=" * 76)
print("3. UNDUH ULANG About.js YANG DIMUAT (dengan cache bypass)")
print("=" * 76)
if about_urls:
    u = about_urls[0]
    try:
        hasil = page.evaluate(f"""async () => {{
            const r = await fetch('{u}', {{cache: 'reload'}});
            const t = await r.text();
            return {{
                url: '{u}'.slice(0, 100),
                status: r.status,
                len: t.length,
                adaEduAi: t.includes('EduAi INOVASI'),
                adaAscensio: t.includes('Ascensio'),
                cuplikan: t.match(/publishername[^,]*/)?.[0] || '(tidak ada)'
            }};
        }}""")
        print(f"  {json.dumps(hasil, indent=1)}")
    except Exception as e:
        print(f"  gagal: {e}")

browser.close()
print("\nSELESAI.")
