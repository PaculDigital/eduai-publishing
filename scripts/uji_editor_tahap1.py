#!/usr/bin/env python3
"""Beri user uji 1 file (lewat FORM, bukan INSERT manual) lalu uji judul tab
di dalam EDITOR.

Jalankan: /opt/data/services/cloakbrowser/.venv/bin/python3 scripts/uji_editor_tahap1.py
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

# dokumen docx kecil untuk diunggah
DOK = Path('/tmp/uji_rebrand_tahap1.docx')


def buat_docx():
    """Buat docx minimal tanpa python-docx (zip + XML)."""
    import zipfile
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
          'content-types">'
          '<Default Extension="rels" ContentType="application/vnd.'
          'openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/word/document.xml" ContentType="application/'
          'vnd.openxmlformats-officedocument.wordprocessingml.document.'
          'main+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/'
            'package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/officeDocument" '
            'Target="word/document.xml"/></Relationships>')
    doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/'
           'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
           'Naskah uji rebranding tahap 1 EduAi INOVASI.'
           '</w:t></w:r></w:p></w:body></w:document>')
    with zipfile.ZipFile(DOK, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct)
        z.writestr('_rels/.rels', rels)
        z.writestr('word/document.xml', doc)
    return DOK


def sq(sql):
    out = subprocess.run(
        ['docker', 'exec', CONTAINER, 'python3', '-c',
         f"import sqlite3,json;c=sqlite3.connect('{DB}');"
         f"print(json.dumps(c.execute({sql!r}).fetchall()))"],
        capture_output=True, text=True, timeout=60)
    return json.loads(out.stdout.strip() or '[]')


buat_docx()
print(f"[dok] dibuat: {DOK} ({DOK.stat().st_size:,} B)")

print("=" * 76)
print("UJI JUDUL TAB DI DALAM EDITOR (browser nyata)")
print("=" * 76)

browser = launch(headless=True)
page = browser.new_page()
page.set_viewport_size({'width': 390, 'height': 844})

# 1. login
page.goto(f'{BASE}/masuk', wait_until='domcontentloaded', timeout=60000)
page.wait_for_timeout(2500)
page.fill('input[name="email"]', EMAIL)
page.fill('input[name="password"]', SANDI)
page.click('button[type="submit"]')
page.wait_for_timeout(5000)
print(f"\n[login] URL: {page.url} | judul: '{page.title()}'")

# 2. unggah file lewat FORM
try:
    inp = page.query_selector('input[type="file"]')
    if inp:
        inp.set_input_files(str(DOK))
        page.wait_for_timeout(6000)
        print("[unggah] file dikirim lewat form")
    else:
        print("[unggah] ⚠️ input file tidak ditemukan")
except Exception as e:
    print(f"[unggah] ⚠️ {e}")

page.goto(f'{BASE}/naskah', wait_until='domcontentloaded', timeout=60000)
page.wait_for_timeout(3000)

fid = sq("SELECT id FROM files WHERE user_id=15 ORDER BY id DESC LIMIT 1")
print(f"\n[berkas] user uji punya: {fid}")

if fid:
    idf = fid[0][0]
    page.goto(f'{BASE}/edit/{idf}', wait_until='domcontentloaded',
              timeout=90000)
    for i in range(25):
        page.wait_for_timeout(2000)
        if page.query_selector('iframe'):
            break
    page.wait_for_timeout(3000)

    t = page.title()
    print(f"\n[EDITOR] judul tab: '{t}'")
    print(f"    ada iframe: {page.query_selector('iframe') is not None}")
    for fr in page.frames[1:]:
        try:
            j = fr.evaluate('document.title')
            if j:
                print(f"    judul dalam iframe: '{j}'")
        except Exception:
            pass
    print(f"\n    masih 'ONLYOFFICE'? "
          f"{'YA ❌' if 'ONLYOFFICE' in t.upper() else 'TIDAK ✅'}")

    f = SHOT / 'rebrand-tahap1-editor.png'
    page.screenshot(path=str(f))
    print(f"📸 {f}")

browser.close()
print("\nSELESAI.")
