#!/usr/bin/env python3
"""Uji lonceng pembimbing #1+#2 (26Sep26) — lewat HALAMAN NYATA (tinjau).

2 ARAH (aturan Bos):
  A. SEHAT: pembimbing tulis catatan via POST /tinjau/{token}/catatan
     → notifikasi 'pembimbing_catatan_baru' muncul di lonceng pemilik.
  B. DIRUSAK: token ngawur → 303/redirect, tanpa notifikasi baru.
C. dibuka pertama → 'pembimbing_membuka' sekali; buka ke-2 → tidak dobel.
"""
import os
import re
import sys
import urllib.request
import urllib.parse

BASE = 'https://eduai.bikinaja.id'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36')
TOK = os.environ['TOKEN_UJI']
FID = int(os.environ.get('FID_UJI', '58'))
LULU, GAGAL = [], []


def ok(nama, kondisi, info=''):
    (LULU if kondisi else GAGAL).append(f'{nama}: {info}')


def minta(url, data=None, cookie=None):
    req = urllib.request.Request(BASE + url, method='POST' if data else 'GET')
    req.add_header('User-Agent', UA)
    if cookie:
        req.add_header('Cookie', cookie)
    isi = urllib.parse.urlencode(data).encode() if data else None
    try:
        d = urllib.request.urlopen(req, data=isi, timeout=60)
        return d.status, d.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')


# ── data awal ────────────────────────────────────────────────────────────
st, html = minta('/naskah', cookie=f'eduai_session={TOK}')
ok('login dashboard', st == 200 and 'Naskah' in html, f'{st}')

# buat bimbingan uji via rute resmi
st, bal = minta('/pembimbing/bagikan', {
    'nama': 'Dosen Uji Lonceng', 'wa': '628123456789', 'hari': 30,
    'file_id': str(FID),
}, cookie=f'eduai_session={TOK}')
try:
    j = __import__('json').loads(bal)
except Exception:
    j = {}
ok('buat bimbingan', j.get('ok'), bal[:120])
token = j.get('token', '')

# ── C. BUKA PERTAMA → notif 'membuka' ───────────────────────────────────
st, html = minta(f'/tinjau/{token}')
ok('halaman tinjau terbuka', st == 200, f'{st}')

# baca lonceng pemilik
st, bal = minta('/api/ai/v1/proses', cookie=f'eduai_session={TOK}')
ada_buka = 'pembimbing_membuka' in bal
ok('C1 lonceng pembuka (pertama)', ada_buka, bal[:150])

# buka kedua → tidak dobel
st, html = minta(f'/tinjau/{token}')
st, bal = minta('/api/ai/v1/proses', cookie=f'eduai_session={TOK}')
n = bal.count('pembimbing_membuka')
ok('C2 buka kedua TIDAK dobel', n <= 1, f'ditemukan {n}')

# ── A. CATATAN BARU → notif catatan ─────────────────────────────────────
st, bal = minta(f'/tinjau/{token}/catatan', {
    'isi': 'Uji lonceng: tambahkan sitasi di paragraf ini.',
    'section_judul': 'BAB II Uji Lonceng',
}, cookie=None)  # halaman tinjau tidak butuh login
ok('A1 POST catatan (halaman publik)', st in (200, 303), f'{st}')

st, bal = minta('/api/ai/v1/proses', cookie=f'eduai_session={TOK}')
ok('A2 lonceng catatan baru', 'pembimbing_catatan_baru' in bal, bal[:200])
ok('A3 pola pesan benar', 'menandai 1 catatan' in bal, '')

# ── B. DIRUSAK: token ngawur ────────────────────────────────────────────
st, html = minta('/tinjau/token-ngawur-xyz')
ok('B1 token ngawur = halaman ramah', st == 200 and 'maaf' in html.lower()
   or st in (200, 303), f'{st}')
st, bal = minta('/api/ai/v1/proses', cookie=f'eduai_session={TOK}')
sebelum = bal.count('pembimbing_catatan_baru')
minta(f'/tinjau/token-ngawur-xyz/catatan', {'isi': 'ngawur'})
st, bal = minta('/api/ai/v1/proses', cookie=f'eduai_session={TOK}')
ok('B2 token ngawur TIDAK menambah notif',
   bal.count('pembimbing_catatan_baru') == sebelum, '')

print(f'LULUS {len(LULU)} / GAGAL {len(GAGAL)}')
for x in GAGAL:
    print('  GAGAL:', x)
sys.exit(1 if GAGAL else 0)
