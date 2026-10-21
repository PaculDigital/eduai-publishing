#!/usr/bin/env python3
"""UJI E2E AI NYATA + blok STANDAR PENULISAN (26Sep26).

Alur: POST /v1/revisi (file_id 58 + naskah teks pendek) → pantau
proses → baca hasil + bukti log "[standar]" di server.
"""
import json
import os
import sys
import time
import urllib.request

BASE = 'https://eduai.bikinaja.id'
TOKEN = os.environ['TOKEN_UJI']
# UA browser (Cloudflare blokir UA bawaan python — error 1010)
_UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
       '(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36')

NASKAH = (
    "BAB I PENDAHULUAN\n\n"
    "1.1 Latar Belakang\n"
    "Penjualan merupakan kegiatan utama perusahaan untuk mempertahankan "
    "kelangsungan bisnisnya. Kinerja pemasaran yang baik sangat menentukan "
    "peningkatan penjualan produk. Penelitian ini dilakukan untuk "
    "menganalisis pengaruh promosi dan kualitas layanan terhadap "
    "peningkatan penjualan pada perusahaan daerah.\n"
)


def post(jalur, badan, tipe='application/json'):
    data = json.dumps(badan).encode() if tipe == 'application/json' else badan
    req = urllib.request.Request(
        BASE + jalur, data=data, method='POST',
        headers={'Content-Type': tipe, 'Cookie': f'eduai_session={TOKEN}',
                 'User-Agent': _UA})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def get(jalur):
    req = urllib.request.Request(
        BASE + jalur, headers={'Cookie': f'eduai_session={TOKEN}',
                               'User-Agent': _UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


# 1. POST revisi
t0 = time.time()
st, d = post('/api/ai/v1/revisi', {
    'file_id': 58,
    'naskah': NASKAH,
    'komentar': ['Rapikan penulisan paragraf ini sesuai aturan pedoman.'],
    'setuju_bagian': True,
})
print('POST revisi:', st, json.dumps(d, ensure_ascii=False)[:300])
kode = (d.get('proses') or d.get('kode') or '').strip()
if not kode:
    print('GAGAL: tidak ada kode proses')
    sys.exit(1)

# 2. Pantau proses
for i in range(60):
    time.sleep(5)
    s, p = get(f'/api/ai/v1/proses/{kode}')
    tahap = p.get('tahap') or p.get('status') or '?'
    print(f'  [{i*5:3d}s] {tahap}')
    if s == 200 and str(p.get('selesai') or '').lower() in ('true', '1') \
            or 'selesai' in str(tahap).lower() or 'done' in str(tahap).lower():
        print('SELESAI dalam', round(time.time() - t0), 's')
        print(json.dumps(p, ensure_ascii=False)[:1200])
        break
else:
    print('BATAS PANTAU habis (300 s)')
    sys.exit(2)
