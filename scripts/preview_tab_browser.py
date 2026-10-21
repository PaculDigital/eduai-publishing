#!/usr/bin/env python3
"""PREVIEW v2: upload docx + buka editor + suntik CSS tab + screenshot.

CSS hanya via add_style_tag (memori browser) — NOL perubahan server.
"""
import re
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
import secrets as _secrets
EMAIL = f'uji-tab-{_secrets.token_hex(3)}@eduai.id'
PASSWORD = 'UjiTab123!'


# ── buat docx minimal via zipfile (tanpa lib eksternal) ───────────────
def buat_docx(nama='Uji Tab.docx'):
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<w:document xmlns:w="http://schemas.openxmlformats.org/'
          'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
          'BAB III METODE PENELITIAN. Penelitian ini menggunakan pendekatan '
          'kuantitatif dengan desain survei.</w:t></w:r></w:p></w:body>'
          '</w:document>')
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
    buf.seek(0)
    return buf.read()


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
        return e   # 303 tetap punya headers


def cookie_dari(r):
    m = re.search(r'(eduai_session=[^;]+)', r.headers.get('Set-Cookie', ''))
    return m.group(1) if m else None


# ── 1. sesi ────────────────────────────────────────────────────────────
ck = None
r = form(f'{BASE}/daftar', {'email': EMAIL, 'password': PASSWORD,
                            'nama': 'Uji Tab'})
ck = cookie_dari(r)
if not ck:
    ck = cookie_dari(form(f'{BASE}/masuk', {'email': EMAIL,
                                             'password': PASSWORD}))
if not ck:
    print('GAGAL sesi'); sys.exit(1)
print('✅ sesi OK')

# ── 2. upload docx ─────────────────────────────────────────────────────
bd = '----wulan' + uuid.uuid4().hex
docx = buat_docx()
parts = []
parts.append(f'--{bd}\r\nContent-Disposition: form-data; name="berkas"; '
             f'filename="Uji Tab.docx"\r\n'
             'Content-Type: application/vnd.openxmlformats-officedocument'
             '.wordprocessingml.document\r\n\r\n'.encode() + docx + b'\r\n')
parts.append(f'--{bd}\r\nContent-Disposition: form-data; name="nama"\r\n'
             '\r\nUji Tab\r\n'.encode())
body = b''.join(parts) + f'--{bd}--\r\n'.encode()
req = urllib.request.Request(f'{BASE}/unggah', data=body, headers={
    'Cookie': ck, 'Content-Type': f'multipart/form-data; boundary={bd}'})
resp = urllib.request.urlopen(req, timeout=120)
print('✅ upload:', resp.read().decode()[:100])

# ── 3. browser: login + buka editor file itu ───────────────────────────
browser = launch(headless=True)
page = browser.new_page()
page.set_viewport_size({'width': 1600, 'height': 900})
page.goto(f'{BASE}/masuk', wait_until='domcontentloaded')
inputs = page.query_selector_all('input')
inputs[0].fill(EMAIL)
inputs[1].fill(PASSWORD)
page.query_selector('button[type=submit]').click()
time.sleep(2)

page.goto(f'{BASE}/naskah', wait_until='domcontentloaded')
time.sleep(1)
edit = page.evaluate("""() => [...document.querySelectorAll('a[href*="edit"]')]
    .map(a => a.getAttribute('href'))""")
print('link edit:', edit[:3])
if not edit:
    browser.close(); sys.exit(1)
page.goto(BASE + edit[0], wait_until='domcontentloaded')

# ── 4. tunggu iframe editor siap (polling, bukan sleep tetap) ───────────
def cari_frame_oo():
    for fr in page.frames[1:]:
        u = fr.url or ''
        if 'documenteditor' in u or '/oo/' in u or 'web-apps' in u:
            return fr
    return None

fr_ai = None
galat = None
for detik in range(90):
    time.sleep(2)
    # cek pesan galat di halaman induk
    galat = page.evaluate("""() => {
        const g = document.getElementById('galat');
        const m = document.getElementById('memuat');
        const ifr = document.querySelector('#tempat-editor iframe');
        return { galatTampil: g ? !g.hidden : false,
                 galatTeks: g ? g.innerText.slice(0, 80) : '',
                 memuat: m ? !m.hidden : null,
                 iframeAda: !!ifr,
                 iframeSrc: ifr ? ifr.src.slice(0, 90) : '' };
    }""")
    if galat['galatTampil']:
        print('❌ editor galat:', galat['galatTeks'])
        break
    for fr in page.frames[1:]:
        u = fr.url or ''
        if 'documenteditor' in u or 'web-apps' in u:
            try:
                ada = fr.evaluate(
                    "() => document.querySelectorAll"
                    "('.box-tabs a[role=tab]').length")
                if ada:
                    fr_ai = fr
                    print(f'✅ editor siap ~{detik*2}s — {ada} tab')
                    break
            except Exception:
                pass
    if fr_ai:
        break
    if detik == 89:
        print('DEBUG akhir:', galat)
if not fr_ai:
    print('Frame editor TIDAK SIAP. Frames:')
    for fr in page.frames:
        print('  -', (fr.url or '')[:90])
    page.screenshot(path=f'{SHOTS}/tab_preview_debug.png')
    browser.close(); sys.exit(1)

# ── 4. probe tab + suntik CSS ──────────────────────────────────────────
CSS = """
/* === PREVIEW SEMENTARA (hanya sesi browser ini) === */
/* Tab Kolaborasi: orange tegas */
.box-tabs li.ribtab[data-layout-name='toolbar-collaboration'] > a {
  color: #ea580c !important;
  font-weight: 600 !important;
}
/* Tab AI: shimmer oranye-emas */
@keyframes eduaiShimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.box-tabs li.ribtab[data-layout-name*='ai'] > a,
.box-tabs a[id*='ai'] {
  background: linear-gradient(90deg, #ea580c 20%, #fbbf24 50%, #ea580c 80%);
  background-size: 200% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent !important;
  font-weight: 700 !important;
  animation: eduaiShimmer 2.6s infinite linear;
}
@media (prefers-reduced-motion: reduce) {
  .box-tabs a[id*='ai'] { animation: none; color: #ea580c !important; }
}
"""
info = fr_ai.evaluate("""() => {
    const list = [...document.querySelectorAll('.box-tabs a[role=tab]')];
    return { jumlah: list.length,
             tabs: list.map(a => ({ id: a.id,
                 teks: (a.dataset.title || a.innerText || '').trim()
                       .slice(0, 16),
                 layout: a.closest('li')?.dataset.layoutName || null }) )
                   .slice(0, 14) };
}""")
fr_ai.add_style_tag(content=CSS)
print('TAB:', info)

time.sleep(2)
import os
os.makedirs(SHOTS, exist_ok=True)

# posisi toolbar tab relatif halaman induk (frame OO di dalam iframe)
pos = fr_ai.evaluate("""() => {
    const t = document.querySelector('.box-tabs');
    if (!t) return null;
    const r = t.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y),
             w: Math.round(r.width), h: Math.round(r.height) };
}""")
print('posisi .box-tabs (dlm frame):', pos)
iframe_box = page.evaluate("""() => {
    const fs = [...document.querySelectorAll('iframe')];
    for (const f of fs) {
        try { if (f.contentDocument && f.contentDocument
                .querySelector('.box-tabs')) {
            const r = f.getBoundingClientRect();
            return { x: Math.round(r.x), y: Math.round(r.y) };
        } } catch (e) {}
    }
    return null;
}""")
print('posisi iframe:', iframe_box)

# CARA PALING PASTI: cari handle elemen <a> tab Kolaborasi dari frame OO
# via content_frame() — bounding_box() sudah absolut thd viewport.
box = None
for fr in page.frames[1:]:
    if 'web-apps' in (fr.url or '') or 'documenteditor' in (fr.url or ''):
        try:
            el = fr.query_selector(
                "li.ribtab[data-layout-name='toolbar-collaboration']")
            if el:
                box = el.bounding_box()
                print('bounding_box Kolaborasi:', box)
                break
        except Exception:
            pass
if box:
    # Screenshot FULL PAGE dulu (terbukti jalan), crop di host pakai PIL —
    # hindari quirk clip Playwright di iframe OO.
    pfull = f'{SHOTS}/tab_preview_page.png'
    page.screenshot(path=pfull)
    print('✅ full page:', pfull)
    try:
        import subprocess
        subprocess.run(['/opt/data/services/eduai-publishing/.venv-cek/'
                        'bin/python', '-c', f"""
from PIL import Image
img = Image.open({pfull!r})
img.crop(({int(box['x'])-400}, {int(box['y'])-14},
          {int(box['x'])+800}, {int(box['y'])+34})).save(
    {f'{SHOTS}/tab_preview_zoom.png'!r})
print('crop OK')
"""], check=True)
        print('✅ zoom crop PIL:', f'{SHOTS}/tab_preview_zoom.png')
    except Exception as e:
        print('⚠️ crop gagal:', e)
else:
    print('⚠️ tidak dapat bounding_box Kolaborasi — pakai manual')
    if pos and iframe_box:
        x = max(0, iframe_box['x'] + pos['x'] - 30)
        y = max(0, iframe_box['y'] + pos['y'] - 25)
        w = min(1600 - x, pos['w'] + 60)
        h = min(60, pos['h'] + 50)
        p2 = f'{SHOTS}/tab_preview_zoom.png'
        page.screenshot(path=p2, clip={'x': x, 'y': y, 'width': w,
                                       'height': h})
        print(f'✅ zoom ({x},{y} {w}x{h}):', p2)
        y2 = max(0, y - 10)
        h2 = min(900 - y2, h + 130)
        p3 = f'{SHOTS}/tab_preview_toolbar.png'
        page.screenshot(path=p3, clip={'x': 0, 'y': y2, 'width': 1600,
                                       'height': h2})
        print('✅ toolbar full:', p3)

p1 = f'{SHOTS}/tab_preview_full.png'
page.screenshot(path=p1, clip={'x': 0, 'y': 0, 'width': 1600,
                               'height': 320})
print('✅ screenshot 1 (atas):', p1)

browser.close()
print('SELESAI — CSS hanya preview sesi, tidak ada file server berubah.')
