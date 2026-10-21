#!/usr/bin/env python3
"""Uji ALUR NYATA Tahap 3.3 lewat HTTP, cookie dibuat pakai fungsi RESMI app.

Tidak mengubah sandi siapa pun — memakai auth.buat_token(user_id) milik app
sendiri, persis seperti yang dilakukan rute /masuk.
"""
import json
import sys
import urllib.request
import urllib.parse
import urllib.error

sys.path.insert(0, '/app')
from app.auth import buat_token                     # noqa: E402
from app.config import SESSION_COOKIE               # noqa: E402
import sqlite3                                      # noqa: E402

BASE = 'http://127.0.0.1:8000'

#  Ambil user yang PUNYA bimbingan + satu file_id-nya.
c = sqlite3.connect('/app/data/eduai.db')
row = c.execute('''SELECT p.user_id, u.email, p.id
                   FROM pembimbingan p JOIN users u ON u.id = p.user_id
                   ORDER BY p.id LIMIT 1''').fetchone()
UID, EMAIL, BID = row
print(f'== Uji alur nyata (user={UID} {EMAIL}, bimbingan={BID}) ==')

TOKEN = buat_token(UID)


def ambil(path):
    req = urllib.request.Request(BASE + path,
                                 headers={'Cookie': f'{SESSION_COOKIE}={TOKEN}'})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')


def kirim(path, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        BASE + path, data=body,
        headers={'Cookie': f'{SESSION_COOKIE}={TOKEN}',
                 'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')


lulus, gagal = [], []


def cek(nama, syarat, info=''):
    (lulus if syarat else gagal).append(nama)
    print(f"  {'OK ' if syarat else 'X  '} {nama}" + (f"  [{info}]" if info else ''))


st, _ = ambil('/naskah')
cek('halaman /naskah bisa dibuka (login sah)', st == 200, str(st))

st, isi = ambil(f'/pembimbing/kunci/{BID}')
d = json.loads(isi)
cek('GET kunci 200 + ok', st == 200 and d.get('ok') is True)
cek('kolom belum_selesai ada', 'belum_selesai' in d, str(d.get('belum_selesai')))
cek('kolom pesan ada', bool(d.get('pesan')))

st, isi = kirim('/pembimbing/kunci', {'bimbingan_id': BID, 'paksa': 0})
d = json.loads(isi)
if d.get('butuh_konfirmasi'):
    print(f"  (minta konfirmasi: {d.get('pesan')[:70]})")
    st, isi = kirim('/pembimbing/kunci', {'bimbingan_id': BID, 'paksa': 1})
    d = json.loads(isi)
cek('kunci berhasil', d.get('ok') is True)

st, isi = ambil(f'/pembimbing/kunci/{BID}')
cek('status terkunci=True', json.loads(isi).get('terkunci') is True)

st, isi = kirim('/pembimbing/buka-kunci', {'bimbingan_id': BID})
cek('buka-kunci ok', json.loads(isi).get('ok') is True)

st, isi = ambil(f'/pembimbing/kunci/{BID}')
cek('status terkunci=False', json.loads(isi).get('terkunci') is False)

st, isi = ambil(f'/pembimbing/arsip/{BID}')
d = json.loads(isi)
cek('arsip 200 + ok', st == 200 and d.get('ok') is True)
cek('arsip punya jumlah & hari', 'jumlah' in d and 'hari' in d,
    f"jumlah={d.get('jumlah')} hari={d.get('hari')}")

#  Pagar: bimbingan orang lain → 403
lain = c.execute('SELECT id FROM pembimbingan WHERE user_id != ? LIMIT 1',
                 (UID,)).fetchone()
if lain:
    st, isi = ambil(f'/pembimbing/kunci/{lain[0]}')
    cek('bimbingan orang lain ditolak (403)', st == 403, str(st))

print(f'\n== HASIL: {len(lulus)} LULUS / {len(gagal)} GAGAL ==')
if gagal:
    for g in gagal:
        print('  X', g)
    sys.exit(1)
