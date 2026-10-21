"""UJI LEWAT HTTP SUNGGUHAN — bukan impor fungsi.

KENAPA: semua uji impor-fungsi SALING SEHAT, tapi E2E layar gagal dgn
    token_in=0. ⇒ Perbedaan HARUS di jalur HTTP (rute /api/ai/v1/revisi,
    autentikasi, background task, atau titik potong kuota).

Uji ini memanggil endpoint sungguhan dgn sesi login NYATA lalu mencetak
respons mentah apa adanya.
"""
import json
import os
import sys

import httpx

BASE = 'https://eduai.bikinaja.id'
EMAIL = 'uji-berbayar-e2e@test.local'
SANDI = 'UjiE2e2026!'
FILE_ID = 49

KOMENTAR = ['Perbaiki kalimat pertama paragraf yang memuat '
            '"Perkembangan pesat teknologi dan transformasi digital" — '
            'buat lebih ringkas.']

c = httpx.Client(base_url=BASE, timeout=120, follow_redirects=True,
                 headers={'User-Agent': 'Mozilla/5.0 (uji Wulan)'})

print('1. login ...')
r = c.post('/api/masuk', json={'email': EMAIL, 'sandi': SANDI})
print(f'   status={r.status_code} · body={r.text[:200]}')
if r.status_code != 200:
    r = c.post('/masuk', data={'email': EMAIL, 'password': SANDI})
    print(f'   (form) status={r.status_code}')

print('\n2. kuota SEBELUM ...')
r = c.get('/api/ai/v1/kuota')
print(f'   status={r.status_code} · {r.text[:200]}')

print('\n3. KIRIM revisi ...')
r = c.post('/api/ai/v1/revisi', json={
    'file_id': FILE_ID,
    'komentar': KOMENTAR,
    'bab': '__seluruh__',
})
print(f'   status={r.status_code}')
print(f'   body  = {r.text[:500]}')
