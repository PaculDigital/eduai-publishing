#!/usr/bin/env python3
"""UJI MESIN PETA HALUS (26Sep26) — 2 ARAH.

Arah 1 (SEHAT) : peta awal ≥5 rekomendasi · revisi acak 0-3 · pagar bekerja.
Arah 2 (DIRUSAK): bikin rusak buatan → mesin HARUS menolak/menahan.
"""
import os, sys, tempfile
os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='uji_peta_')
sys.path.insert(0, '/app')
from app import peta_halus as P

L = GA = 0


def cek(nama, syarat, bukti=''):
    global L, GA
    if syarat:
        L += 1
        print(f'  ✅ {nama}')
    else:
        GA += 1
        print(f'  ❌ {nama}  {bukti}')


BAB5 = [
    {'bab': '1', 'judul': 'PENDAHULUAN'},
    {'bab': '2', 'judul': 'TINJAUAN PUSTAKA'},
    {'bab': '3', 'judul': 'METODE PENELITIAN'},
    {'bab': '4', 'judul': 'HASIL DAN PEMBAHASAN'},
    {'bab': '5', 'judul': 'KESIMPULAN DAN SARAN'},
]

print('══ UJI MESIN PETA HALUS ══')

print('\n── A. PETA AWAL: minimal 5 (putusan Bos) ──')
r = P.susun(BAB5, mode='peta_awal', bibit_acak=1)
cek('A1. jumlah >= 5', r['jumlah'] >= 5, str(r['jumlah']))
cek('A2. tidak diam', r['diam'] is False, str(r['diam']))
cek('A3. ada pesan ramah', bool(r['pesan']), str(r['pesan'])[:40])
cek('A4. tiap item punya id+bab+masalah',
    all(d.get('id') and d.get('bab') and d.get('masalah') for d in r['daftar']),
    str(r['daftar'][:1]))
cek('A5. terurut bab naik',
    [d['bab'] for d in r['daftar']] == sorted(d['bab'] for d in r['daftar']),
    str([d['bab'] for d in r['daftar']]))

print('\n── B. PETA AWAL dgn naskah minim (1 bab) → tetap >=5 ──')
r1 = P.susun([{'bab': '1', 'judul': 'PENDAHULUAN'}], mode='peta_awal', bibit_acak=2)
cek('B1. tetap >=5 (dilengkapi bab lain)', r1['jumlah'] >= 5, str(r1['jumlah']))

print('\n── C. PETA AWAL tanpa bab terdeteksi → tetap >=5 ──')
r0 = P.susun([], mode='peta_awal', bibit_acak=3)
cek('C1. tetap >=5', r0['jumlah'] >= 5, str(r0['jumlah']))

print('\n── D. PETA AWAL dibatasi maks 12 (tidak kebanjiran) ──')
r2 = P.susun(BAB5, mode='peta_awal', bibit_acak=4)
cek('D1. jumlah <= 12', r2['jumlah'] <= 12, str(r2['jumlah']))

print('\n── E. PAGAR C1: yang sudah ditawarkan TIDAK muncul lagi ──')
sudah = {d['id'] for d in r2['daftar'][:3]}
r3 = P.susun(BAB5, mode='peta_awal', sudah_ditawarkan=sudah, bibit_acak=4)
cek('E1. id lama tidak muncul',
    not (sudah & {d['id'] for d in r3['daftar']}),
    str(sudah & {d['id'] for d in r3['daftar']}))

print('\n── F. PAGAR C3: yang sudah DITOLAK tidak muncul lagi ──')
ditolak = {d['id'] for d in r2['daftar'][:2]}
r4 = P.susun(BAB5, mode='peta_awal', sudah_ditolak=ditolak, bibit_acak=4)
cek('F1. id ditolak tidak muncul',
    not (ditolak & {d['id'] for d in r4['daftar']}),
    str(ditolak & {d['id'] for d in r4['daftar']}))

print('\n── G. REVISI: maks 3 (aturan lama natural) ──')
maks_salah = []
diam_ada = False
for bibit in range(40):
    rr = P.susun(BAB5, mode='revisi', bibit_acak=bibit)
    if rr['jumlah'] > 3:
        maks_salah.append(rr['jumlah'])
    if rr['diam']:
        diam_ada = True
cek('G1. tidak pernah > 3', not maks_salah, str(maks_salah[:3]))
cek('G2. kadang DIAM (natural, 0-3)', diam_ada, 'tidak ada yang diam')

print('\n── H. REVISI DIAM → pesan ramah (pagar C4) ──')
diam = None
for bibit in range(60):
    rr = P.susun(BAB5, mode='revisi', bibit_acak=bibit)
    if rr['diam']:
        diam = rr
        break
cek('H1. pesan diam = "Sudah bagus…"',
    diam is not None and 'bagus' in (diam.get('pesan') or '').lower(),
    str(diam and diam.get('pesan')))

print('\n── I. SIDIK NASKAH (pagar C2) ──')
s1 = P.sidik_naskah('naskah A')
s2 = P.sidik_naskah('naskah A')
s3 = P.sidik_naskah('naskah B')
cek('I1. naskah sama → sidik sama', s1 == s2, f'{s1[:8]} vs {s2[:8]}')
cek('I2. naskah beda → sidik beda', s1 != s3, f'{s1[:8]} vs {s3[:8]}')
cek('I3. boleh dipakai ulang saat naskah tak berubah',
    P.boleh_pakai_ulang(s1, 'naskah A') is True, '')
cek('I4. TIDAK boleh saat naskah berubah',
    P.boleh_pakai_ulang(s1, 'naskah B') is False, '')
cek('I5. tanpa sidik → tidak boleh', P.boleh_pakai_ulang('', 'x') is False, '')

print('\n── J. 🔴 DIRUSAK: mode ngawur → jangan meledak ──')
try:
    rd = P.susun(BAB5, mode='ngawur', bibit_acak=1)
    cek('J1. mode ngawur tetap jalan (dianggap peta_awal)', rd['jumlah'] >= 5,
        str(rd['jumlah']))
except Exception as e:  # noqa
    cek('J1. mode ngawur tetap jalan', False, repr(e)[:60])

print('\n── K. 🔴 DIRUSAK: bab terdeteksi rusak (bukan list) ──')
try:
    rk = P.susun('bukan list', mode='peta_awal', bibit_acak=1)  # type: ignore
    cek('K1. tetap jalan tanpa meledak', rk['jumlah'] >= 5, str(rk['jumlah']))
except Exception as e:  # noqa
    cek('K1. tetap jalan tanpa meledak', False, repr(e)[:60])

print('\n── L. 🔴 DIRUSAK: bab tanpa kunci "bab" ──')
try:
    rl = P.susun([{'judul': 'X'}, {'bab': '3', 'judul': 'METODE'}],
                 mode='peta_awal', bibit_acak=1)
    cek('L1. item rusak dilewati, tetap >=5', rl['jumlah'] >= 5, str(rl['jumlah']))
except Exception as e:  # noqa
    cek('L1. item rusak dilewati', False, repr(e)[:60])

print('\n── M. TAMPILAN ringkas (bentuk yang dibaca user) ──')
t = P.ringkas(r2)
cek('M1. ada judul PETA', 'PETA' in t, t[:60])
cek('M2. ada nama BAB', 'BAB' in t, t[:80])
print('\n' + t[:600])

print(f'\n══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
