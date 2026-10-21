#!/usr/bin/env python3
"""DEBUG frame editor — kenapa tidak siap."""
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
EMAIL = f'verif-tab-{secrets.token_hex(3)}@eduai.id'
PASSWORD = 'UjiTab123!'


def buat_docx():
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<w:document xmlns:w="http://schemas.openxmlformats.org/'
          'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
          'Uji debug frame.</w:t></w:r></w:p></w:body></w:document>')
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


ck = cookie_dari(form(f'{BASE}/daftar', {'email': EMAIL,
                                         'password': PASSWORD,
                                         'nama': 'Dbg'}))
if not ck:
    ck = cookie_dari(form(f'{BASE}/masuk', {'email': EMAIL,
                                            'password': PASSWORD}))
print('sesi:', 'OK' if ck else 'GAGAL')

bd = '----wulan' + uuid.uuid4().hex
parts = [f'--{bd}\r\nContent-Disposition: form-data; name="berkas"; '
         f'filename="Dbg.docx"\r\nContent-Type: application/vnd.'
         'openxmlformats-officedocument.wordprocessingml.document\r\n\r\n'
         .encode() + buat_docx() + b'\r\n',
         f'--{bd}\r\nContent-Disposition: form-data; name="nama"\r\n'
         '\r\nDbg\r\n'.encode()]
body = b''.join(parts) + f'--{bd}--\r\n'.encode()
req = urllib.request.Request(f'{BASE}/unggah', data=body, headers={
    'Cookie': ck, 'Content-Type': f'multipart/form-data; boundary={bd}'})
print('upload:', urllib.request.urlopen(req, timeout=120).read().decode()[:80])

browser = launch(headless=True)
page = browser.new_page()
page.set_viewport_size({'width': 1600, 'height': 900})
page.goto(f'{BASE}/masuk', wait_until='domcontentloaded')
ins = page.query_selector_all('input')
ins[0].fill(EMAIL)
ins[1].fill(PASSWORD)
page.query_selector('button[type=submit]').click()
time.sleep(2)
page.goto(f'{BASE}/naskah', wait_until='domcontentloaded')
time.sleep(2)
edits = page.evaluate("""() => [...document.querySelectorAll('a')]
    .map(a => a.getAttribute('href')).filter(h => h && h.includes('edit'))""")
print('link edit:', edits[:5])
print('semua link:', page.evaluate("""() => [...document.querySelectorAll('a')]
    .map(a => a.getAttribute('href')).filter(Boolean).slice(0, 25)"""))

if edits:
    page.goto(BASE + edits[0], wait_until='domcontentloaded')
    for i in range(15):
        time.sleep(2)
        frames = [(f.url or '')[:100] for f in page.frames]
        print(f'--- t={i*2}s frames={len(frames)} ---')
        for f in frames:
            print('   ', f)
        st = page.evaluate("""() => ({
            galat: document.getElementById('galat') ?
                   !document.getElementById('galat').hidden : null,
            galatTeks: document.getElementById('galat') ?
                   document.getElementById('galat').innerText.slice(0,120) : '',
            memuat: document.getElementById('memuat') ?
                   !document.getElementById('memuat').hidden : null,
            iframe: !!document.querySelector('#tempat-editor iframe')
        })""")
        print('   state:', st)
        if len(frames) > 1:
            break
    page.screenshot(path='/opt/data/services/eduai-publishing/shots/dbg_frame.png')
    print('screenshot: shots/dbg_frame.png')
page.screenshot(path='/opt/data/services/eduai-publishing/shots/dbg_naskah.png')
browser.close()
