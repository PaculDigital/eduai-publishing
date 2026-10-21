#!/usr/bin/env python3
"""DIAGNOSA: kenapa login gagal? Tangkap pesan error di halaman masuk."""
import json, os, sys
from cloakbrowser import launch

BASE = 'https://eduai.bikinaja.id'
EMAIL = os.environ.get('UJI_EMAIL', 'uji.lengkap@eduai.local')
SANDI = os.environ.get('UJI_SANDI', 'ujiLengkap12345')

b = launch(headless=True)
ctx = b.new_context(viewport={'width': 1440, 'height': 900}, ignore_https_errors=True)
p = ctx.new_page()

p.goto(f'{BASE}/masuk', wait_until='domcontentloaded', timeout=60000)
p.wait_for_timeout(3000)

# isi form
p.fill('input[name="email"]', EMAIL)
p.fill('input[name="password"]', SANDI)

# tangkap semua respons setelah submit
respon = []
p.on('response', lambda r: respon.append((r.status, r.url)) if r.request.method == 'POST' else None)

p.click('button[type="submit"]')
p.wait_for_timeout(6000)

out = {
    'url_akhir': p.url,
    'respon_POST': respon[-5:],
    'teks_halaman': p.inner_text('body')[:700],
}
p.screenshot(path='/opt/data/services/eduai-publishing/shots/diag-login.png')
print(json.dumps(out, indent=1, ensure_ascii=False))
b.close()
