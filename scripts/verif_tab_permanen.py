#!/usr/bin/env python3
"""VERIFIKASI PERMANEN: cek warna tab Kolaborasi TANPA suntik CSS.

Bedanya dengan preview_tab_browser.py:
  - TIDAK ada add_style_tag sama sekali (kalau warna muncul, berarti
    benar-benar dari file app.css di server / permanen).
  - Membaca getComputedStyle + membandingkan warna tab lain sebagai kontrol.
"""
import json
import os
import re
import secrets
import sys
import time
import urllib.parse
import urllib.request
import uuid
import io
import zipfile

from cloakbrowser import launch

BASE = 'http://172.17.0.8:8000'
SHOTS = '/opt/data/services/eduai-publishing/shots'
EMAIL = f'verif-tab-{secrets.token_hex(3)}@eduai.id'
PASSWORD = 'UjiTab123!'
TARGET = '#ffa000'
TARGET_RGB = (255, 160, 0)


def buat_docx():
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<w:document xmlns:w="http://schemas.openxmlformats.org/'
          'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
          'BAB III METODE PENELITIAN. Uji permanen warna tab.</w:t></w:r>'
          '</w:p></w:body></w:document>')
    cp = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
          'content-types"><Default Extension="rels" ContentType="application/'
          'vnd.openxmlformats-package.relationships+xml"/><Default '
          'Extension="xml" ContentType="application/xml"/><Override '
          'PartName="/word/document.xml" ContentType="application/'
          'vnd.openxmlformats-officedocument.wordprocessingml.document.'
          'main+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/'
            'package/2006/relationships"><Relationship Id="rId1" Type='
            '"http://schemas.openxmlformats.org/officeDocument/2006/'
            'relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', cp)
        z.writestr('_rels/.rels', rels)
        z.writestr('word/document.xml', ct)
    return buf.getvalue()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def form(url, data, cookie=None):
    body = urllib.parse.urlencode(data).encode()
    h = {'Content-Type': 'application/x-www-form-urlencoded'}
    if cookie:
        h['Cookie'] = cookie
    req = urllib.request.Request(url, data=body, headers=h)
    try:
        return urllib.request.build_opener(NoRedirect).open(req, timeout=60)
    except urllib.error.HTTPError as e:
        return e


def cookie_dari(r):
    m = re.search(r'(eduai_session=[^;]+)', r.headers.get('Set-Cookie', ''))
    return m.group(1) if m else None


# ── 1. sesi ────────────────────────────────────────────────────────────
ck = cookie_dari(form(f'{BASE}/daftar', {'email': EMAIL, 'password': PASSWORD,
                                         'nama': 'Verif Tab'}))
if not ck:
    ck = cookie_dari(form(f'{BASE}/masuk', {'email': EMAIL, 'password': PASSWORD}))
if not ck:
    print('GAGAL sesi'); sys.exit(1)
print('✅ sesi OK')

# ── 2. upload ──────────────────────────────────────────────────────────
bd = '----wulan' + uuid.uuid4().hex
parts = [f'--{bd}\r\nContent-Disposition: form-data; name="berkas"; '
         f'filename="Verif Tab.docx"\r\n'
         'Content-Type: application/vnd.openxmlformats-officedocument'
         '.wordprocessingml.document\r\n\r\n'.encode() + buat_docx() + b'\r\n',
         f'--{bd}\r\nContent-Disposition: form-data; name="nama"\r\n'
         '\r\nVerif Tab\r\n'.encode()]
body = b''.join(parts) + f'--{bd}--\r\n'.encode()
req = urllib.request.Request(f'{BASE}/unggah', data=body, headers={
    'Cookie': ck, 'Content-Type': f'multipart/form-data; boundary={bd}'})
print('✅ upload:', urllib.request.urlopen(req, timeout=120).read().decode()[:80])

# ── 3. browser ─────────────────────────────────────────────────────────
browser = launch(headless=True)
try:
    page = browser.new_page()
    page.set_viewport_size({'width': 1600, 'height': 900})
    page.goto(f'{BASE}/masuk', wait_until='domcontentloaded')
    ins = page.query_selector_all('input')
    ins[0].fill(EMAIL)
    ins[1].fill(PASSWORD)
    page.query_selector('button[type=submit]').click()
    time.sleep(2)
    page.goto(f'{BASE}/naskah', wait_until='domcontentloaded')
    time.sleep(1)
    edits = page.evaluate("""() => [...document.querySelectorAll('a[href*="edit"]')]
        .map(a => a.getAttribute('href'))""")
    if not edits:
        print('GAGAL: tidak ada link edit'); sys.exit(1)
    page.goto(BASE + edits[0], wait_until='domcontentloaded')

    fr = None
    for _ in range(90):
        time.sleep(2)
        for f in page.frames[1:]:
            u = f.url or ''
            if 'documenteditor' in u or 'web-apps' in u:
                try:
                    if f.evaluate("() => document.querySelectorAll"
                                  "('.box-tabs a[role=tab]').length"):
                        fr = f
                        break
                except Exception:
                    pass
        if fr:
            break
    if not fr:
        print('GAGAL: frame editor tidak siap'); sys.exit(1)
    print('✅ editor siap — TANPA add_style_tag')

    # tunggu tab ter-render penuh
    time.sleep(3)

    # ── 4. BACA getComputedStyle (tanpa suntik apa pun) ────────────────
    hasil = fr.evaluate("""() => {
        const tabs = [...document.querySelectorAll('.box-tabs a[role=tab]')];
        return tabs.map(a => {
            const cs = getComputedStyle(a);
            const li = a.closest('li');
            return {
                id: a.id,
                dataTab: a.getAttribute('data-tab'),
                layout: li ? (li.dataset.layoutName || null) : null,
                teks: (a.dataset.title || a.innerText || '').trim(),
                color: cs.color,
                weight: cs.fontWeight,
                shadow: cs.textShadow ? cs.textShadow.slice(0, 40) : 'none',
            };
        });
    }""")
    print('\n=== TAB YANG TER-RENDER (getComputedStyle, TANPA CSS suntikan) ===')
    for t in hasil:
        print(json.dumps(t, ensure_ascii=False))

    # kontrol: cari tab Kolaborasi
    kol = [t for t in hasil if t.get('layout') == 'toolbar-collaboration'
           or t.get('dataTab') == 'review'
           or t.get('teks', '').lower().startswith('kolab')]
    print(f'\n=== HASIL ===')
    if not kol:
        print('❌ Tab Kolaborasi TIDAK ketemu di render')
        for t in hasil:
            print('   -', t['id'], t['dataTab'], t['layout'], t['teks'])
        page.screenshot(path=f'{SHOTS}/verif_permanen_debug.png')
    else:
        t = kol[0]
        print(f"   tab       : id={t['id']} data-tab={t['dataTab']} layout={t['layout']}")
        print(f"   warna     : {t['color']}  (target {TARGET})")
        print(f"   bold      : {t['weight']}")
        print(f"   textShadow: {t['shadow']}")
        cocok = t['color'].replace(' ', '') == f'rgb{TARGET_RGB}'.replace(' ', '')
        print(f"   {'✅ COCOK' if cocok else '❌ TIDAK COCOK'} — permanen dari server")
        # bandingkan dengan tab lain
        lain = [x for x in hasil if x is not t][:4]
        print('   pembanding:')
        for x in lain:
            print(f"      {x['teks'][:14]:16} {x['color']:20} weight={x['weight']}")

    # screenshot bar tab
    box = fr.evaluate("""() => {
        const li = document.querySelector("li.ribtab[data-layout-name='toolbar-collaboration']");
        const t = document.querySelector('.box-tabs');
        const r = (li || t).getBoundingClientRect();
        const tr = t ? t.getBoundingClientRect() : r;
        return { x: Math.round(tr.x), y: Math.round(tr.y),
                 w: Math.round(tr.width), h: Math.round(tr.height) };
    }""")
    print('\nposisi bar tab:', box)
    page.screenshot(path=f'{SHOTS}/verif_permanen_page.png')
    print('✅ screenshot:', f'{SHOTS}/verif_permanen_page.png')
    try:
        from PIL import Image
        img = Image.open(f'{SHOTS}/verif_permanen_page.png')
        pad = 6
        img.crop((max(0, box['x'] - pad), max(0, box['y'] - pad),
                  min(img.width, box['x'] + box['w'] + pad),
                  min(img.height, box['y'] + box['h'] + pad))).save(
            f'{SHOTS}/verif_permanen_tabbar.png')
        print('✅ crop bar tab:', f'{SHOTS}/verif_permanen_tabbar.png')
    except Exception as e:
        print('⚠️ crop gagal:', e)
finally:
    browser.close()
