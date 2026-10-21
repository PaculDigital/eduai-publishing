#!/usr/bin/env python3
"""BUKTI ANTI-SPAM M1 (05Okt26) — jalan DI DALAM container eduai-app.

Pertanyaan: 429 pada M1 = anti-spam BENAR, atau bug?

Rute BENAR (dari kode, bukan karangan):
  login    : POST /masuk (form email+password)
  unggah   : POST /unggah (multipart, field `berkas`)
  revisi   : POST /api/ai/v1/revisi (router prefix '/api/ai')

Bukti 2 arah: revisi-1 → tunggu 70 dtk (jatah 6/60dtk pulih) → revisi-2.
Kalau revisi-2 = 200 → ANTI-SPAM BENAR (429 tadi bukan bug).
"""
from __future__ import annotations

import http.cookiejar
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import uuid

BASE = os.getenv('E2E_BASE', 'http://127.0.0.1:8000')
EMAIL = 'uji-berat-e2e@test.local'
SANDI = 'UjiBerat123!'

cj = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cj),
    urllib.request.HTTPRedirectHandler())


def buka(path: str, data=None, metode: str = 'GET', timeout: int = 300):
    url = BASE + path
    headers = {}
    if isinstance(data, bytes):
        headers['Content-Type'] = 'multipart/form-data; boundary=' + BND
    elif data is not None:
        data = urllib.parse.urlencode(data).encode()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    req = urllib.request.Request(url, data=data, method=metode, headers=headers)
    try:
        with OP.open(req, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:                                     # noqa: BLE001
        return 0, f'{type(e).__name__}: {e}'


BND = '----uji' + uuid.uuid4().hex[:12]


def multipart(nama_berkas: str, isi: bytes) -> bytes:
    """Badan multipart untuk POST /unggah (field `berkas`)."""
    b = io.BytesIO()
    b.write(f'--{BND}\r\n'.encode())
    b.write(f'Content-Disposition: form-data; name="berkas"; '
            f'filename="{nama_berkas}"\r\n'.encode())
    b.write(b'Content-Type: application/octet-stream\r\n\r\n')
    b.write(isi)
    b.write(f'\r\n--{BND}--\r\n'.encode())
    return b.getvalue()


print('════ BUKTI ANTI-SPAM M1 ════')
s, b = buka('/masuk', {'email': EMAIL, 'password': SANDI}, 'POST')
print(f'1. login   : HTTP {s} · cookie={[c.name for c in cj]}')
if 'eduai_session' not in [c.name for c in cj]:
    print('   ❌ login gagal'); sys.exit(1)

#  ⚠️ Cara paling langsung: pakai file_id yang SUDAH ADA milik user uji
#     (tidak perlu unggah). Tabel = `files` (bukan `file_berkas`).
fid = int(os.getenv('E2E_FILE_ID', '104'))
print(f'2. pakai file_id yang sudah ada: {fid}')

body = {'komentar': ['Perbaiki tata bahasa dan ejaan paragraf.'],
        'file_id': fid, 'setuju_bagian': True}

for ke in (1, 2):
    t0 = time.monotonic()
    s, b = buka('/api/ai/v1/revisi', body, 'POST', timeout=300)
    dt = time.monotonic() - t0
    kode = ''
    try:
        kode = (json.loads(b) or {}).get('kode') or ''
    except Exception:                                          # noqa: BLE001
        pass
    print(f'{2+ke}. revisi-{ke}: HTTP {s} · {dt:.1f}s · kode={kode or "-"}')
    print(f'   isi: {b[:300]}')
    if ke == 1:
        print('   tunggu 70s (jatah rate-limit 6/60s/user pulih)…')
        time.sleep(70)

print('════ SELESAI ════')
