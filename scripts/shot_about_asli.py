#!/usr/bin/env python3
"""Ambil screenshot ASLI dialog About OnlyOffice (yang sekarang tampil ke user).

Karena kita mematikan About ('about': False), dialog TIDAK muncul.
Untuk keperluan DISKUSI, script ini membuka OO LANGSUNG (tanpa proxy kita)
supaya dialog About terbuka dengan data default OO.

CATATAN: akses langsung ke oo-converter lewat 172.17.0.1:<port OO> agar
tidak lewat kode kita yang mematikan About.
"""
import json
import subprocess
from pathlib import Path

from cloakbrowser import launch

SHOT = Path('/opt/data/services/eduai-publishing/shots')
CONTAINER = 'oo-converter'


def sh(cmd, timeout=60):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip()


# cek port OO di host
for p in [18081, 8081, 8080]:
    out = sh(f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 5 "
             f"http://172.17.0.1:{p}/healthcheck")
    print(f"port {p}: HTTP {out}")

PORT = 80
BASE = f'http://172.17.0.7'

print("=" * 74)
print(f"AMBIL SCREENSHOT ABOUT (langsung ke OO: {BASE})")
print("=" * 74)

browser = launch(headless=True)
page = browser.new_page()
page.set_viewport_size({'width': 1440, 'height': 900})

# halaman index OO punya tombol About di panel kiri
url = f'{BASE}/web-apps/apps/documenteditor/main/index.html'
print(f"\nbuka: {url}")
try:
    page.goto(url, wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(8000)
    print(f"judul: '{page.title()}'")
    f1 = SHOT / 'about-asli-01-index.png'
    page.screenshot(path=str(f1))
    print(f"📸 {f1}")

    # cari tombol About
    info = page.evaluate("""() => {
        const o = [];
        document.querySelectorAll('#left-btn-about, [id*="about"]').forEach(e => {
            const r = e.getBoundingClientRect();
            o.push({id: e.id, tag: e.tagName,
                    x: Math.round(r.x + r.width/2),
                    y: Math.round(r.y + r.height/2),
                    w: Math.round(r.width), h: Math.round(r.height)});
        });
        return o;
    }""")
    print(f"\n[elemen about] {json.dumps(info, indent=1)}")

    # klik via koordinat (paling andal untuk OO)
    for el in info:
        if el['w'] > 0 and el['h'] > 0:
            print(f"\nklik di ({el['x']}, {el['y']}) id={el['id']}")
            page.mouse.click(el['x'], el['y'])
            page.wait_for_timeout(3500)
            f2 = SHOT / 'about-asli-02.png'
            page.screenshot(path=str(f2))
            print(f"📸 {f2}")
            break

    # kalau perlu klik tombol info lagi (kadang 2x)
    page.wait_for_timeout(1500)
    f3 = SHOT / 'about-asli-03.png'
    page.screenshot(path=str(f3))
    print(f"📸 {f3}")

except Exception as e:
    print(f"❌ {e}")

browser.close()
print("\nSELESAI.")
