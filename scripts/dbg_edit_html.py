#!/usr/bin/env python3
"""DEBUG: kenapa iframe editor tidak terpasang di /edit/<id>."""
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
EMAIL = f'dbg-frame-{secrets.token_hex(3)}@eduai.id'
PASSWORD = 'UjiTab123!'


def buat_docx():
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<w:document xmlns:w="http://schemas.openxmlformats.org/'
          'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Dbg.</w:t>'
          '</w:r></w:p></w:body></w:document>')
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


ck = cookie_dari(form(f'{BASE}/daftar', {'email': EMAIL, 'password': PASSWORD,
                                         'nama': 'DbgF'}))
if not ck:
    ck = cookie_dari(form(f'{BASE}/masuk', {'email': EMAIL,
                                            'password': PASSWORD}))
print('sesi:', 'OK' if ck else 'GAGAL')
print('cookie:', ck[:40] if ck else None)

bd = '----wulan' + uuid.uuid4().hex
parts = [f'--{bd}\r\nContent-Disposition: form-data; name="berkas"; '
         f'filename="DbgF.docx"\r\nContent-Type: application/vnd.'
         'openxmlformats-officedocument.wordprocessingml.document\r\n\r\n'
         .encode() + buat_docx() + b'\r\n',
         f'--{bd}\r\nContent-Disposition: form-data; name="nama"\r\n'
         '\r\nDbgF\r\n'.encode()]
body = b''.join(parts) + f'--{bd}--\r\n'.encode()
req = urllib.request.Request(f'{BASE}/unggah', data=body, headers={
    'Cookie': ck, 'Content-Type': f'multipart/form-data; boundary={bd}'})
print('upload:', urllib.request.urlopen(req, timeout=120).read().decode()[:80])

# AMBIL /edit/<id> PAKAI COOKIE (tanpa browser) → lihat HTML & konfig
import json
print('\n=== GET /naskah untuk cari id ===')
r = urllib.request.Request(f'{BASE}/naskah', headers={'Cookie': ck})
html = urllib.request.urlopen(r, timeout=30).read().decode('utf-8', 'ignore')
ids = re.findall(r'/edit/(\d+)', html)
print('id ditemukan:', ids)

if ids:
    fid = ids[0]
    r = urllib.request.Request(f'{BASE}/edit/{fid}', headers={'Cookie': ck})
    try:
        resp = urllib.request.urlopen(r, timeout=60)
        h = resp.read().decode('utf-8', 'ignore')
        print(f'\n=== /edit/{fid} status {resp.status} panjang {len(h)} ===')
        # cari bagian konfigurasi / iframe / error
        for pola, nama in [(r'DocsAPI', 'DocsAPI'),
                           (r'<iframe', 'iframe'),
                           (r'galat', 'galat'),
                           (r'config', 'config'),
                           (r'documentType', 'documentType'),
                           (r'key', 'key')]:
            for m in re.finditer(pola, h):
                cuplik = h[max(0, m.start()-100):m.start()+220]
                print(f'--- [{nama}] ---')
                print(cuplik.replace('\n', ' ')[:320])
                break
    except urllib.error.HTTPError as e:
        print(f'/edit/{fid} HTTP {e.code}')
        print(e.read().decode('utf-8', 'ignore')[:500])
