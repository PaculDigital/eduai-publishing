"""BUKTI IMPOR ronde 1 (opt3) — NOL panggilan Jev.

Jalankan DI DALAM container eduai-app:
    python3 -u /tmp/jev-opt3/bukti_impor.py

Tujuan: buktikan SEBELUM run live bahwa impor MALAS di peta3_jev
(_stitch_baris -> app.sambung_kode, _susun_dari_bersih ->
perbaiki_spasi_huruf / perbaiki_fragmen_huruf, profil_kampus)
jatuh ke scratch /tmp/jev-opt3 (kode v8), BUKAN ke /app (deploy v7).

Caranya: impor EAGER semua modul itu SEBELUM app.hakim_peta (yang
menyisipkan '/app' di posisi 0 sys.path), lalu assert __file__ SEMUA
modul diawali /tmp/jev-opt3/. Sesudah hakim dimuat, periksa lagi
sys.modules — modul yang sudah dimuat TIDAK boleh berganti.

Bukti fungsi (tanpa Jev): sambung_kode('Kalimat pertama yang belum
selesai', 'dan berlanjut di sini.') HARUS True (aturan JOIN v8:
B diawali huruf kecil). Bila bukan True -> exit 1, JANGAN jalankan
run live.

Juga: RULE_VERSION harus 'jev-peta-v8', MODEL_DEFAULT 1.14, dan sidik
DB (files, proses_ai, MAX(id)) stabil selama 5 detik (tidak ada job
live yang sedang menulis — bila berubah, hanya peringatan, bukan
gagal, karena sidik per run tetap di-assert di pelari live).
"""
import os
import sys

os.environ['EDUAI_JEV_CACHE_MAX'] = '0'

sys.path.insert(0, '/tmp/jev-opt3')
os.chdir('/tmp/jev-opt3')

import time

# EAGER: semua modul yang diimpor MALAS di dalam peta3_jev — SEBELUM hakim.
import peta3_jev as P
import app.jev as _J
import app.konversi as K
import app.satpam as S
import app.sambung_kode as SK
import app.profil_kampus as PK
import app.hakim_peta as H

MODUL = {'peta3_jev': P, 'app.jev': _J, 'app.konversi': K,
         'app.satpam': S, 'app.sambung_kode': SK,
         'app.profil_kampus': PK, 'app.hakim_peta': H}
print('--- __file__ tiap modul (harus /tmp/jev-opt3/...) ---', flush=True)
gagal = []
for nama, m in MODUL.items():
    f = getattr(m, '__file__', '?')
    print('  %-18s %s' % (nama, f), flush=True)
    if not str(f).startswith('/tmp/jev-opt3/'):
        gagal.append('%s BUKAN dari scratch: %s' % (nama, f))
print('RULE_VERSION:', P.RULE_VERSION, flush=True)
print('MODEL_DEFAULT:', _J.MODEL_DEFAULT, flush=True)
if P.RULE_VERSION != 'jev-peta-v8':
    gagal.append('RULE_VERSION BUKAN v8: %r' % P.RULE_VERSION)
if _J.MODEL_DEFAULT != 'SATPAM/typesafe/jev-1.14':
    gagal.append('MODEL_DEFAULT BUKAN 1.14: %r' % _J.MODEL_DEFAULT)

# Modul di sys.modules sesudah hakim dimuat: harus tetap yang scratch.
print('--- sys.modules sesudah hakim_peta dimuat ---', flush=True)
for nama in ('app.sambung_kode', 'app.profil_kampus', 'app.jev',
             'app.konversi', 'app.satpam'):
    f = getattr(sys.modules.get(nama), '__file__', '?')
    print('  %-18s %s' % (nama, f), flush=True)
    if not str(f).startswith('/tmp/jev-opt3/'):
        gagal.append('sys.modules %s BUKAN dari scratch: %s' % (nama, f))

# Bukti fungsi v8 (0 Jev): JOIN B-huruf-kecil.
print('--- bukti fungsi sambung_kode (0 Jev) ---', flush=True)
sk = SK.sambung_kode('Kalimat pertama yang belum selesai',
                     'dan berlanjut di sini.')
print('  sk(Kalimat pertama yang belum selesai / dan berlanjut di sini.) = %r'
      % sk, flush=True)
print('  sambung_kode dari modul: %s' % SK.__file__, flush=True)
if sk is not True:
    gagal.append('sambung_kode probe BUKAN True: %r (kode v7 termuat!)' % sk)
# Fungsi huruf (dipakai _susun_dari_bersih): modulnya harus scratch juga.
t, n = SK.perbaiki_spasi_huruf('D i n a m i k a   P a s a r')
print('  perbaiki_spasi_huruf("D i n a m i k a   P a s a r") = %r (%d)'
      % (t, n), flush=True)
print('  perbaiki_spasi_huruf dari modul: %s' % SK.__file__, flush=True)

# Sidik DB 2x (jeda 5 dtk): deteksi job live yang sedang menulis.
from app import ai as _ai
from sqlalchemy import text as _text


def sidik():
    s = _ai.SessionLocal()
    try:
        return (s.execute(_text('SELECT COUNT(*) FROM files')).scalar(),
                s.execute(_text('SELECT COUNT(*) FROM proses_ai')).scalar(),
                s.execute(_text('SELECT MAX(id) FROM proses_ai')).scalar())
    finally:
        s.close()


s1 = sidik()
time.sleep(5)
s2 = sidik()
print('sidik DB t0:', s1, '| t+5dtk:', s2,
      '| STABIL' if s1 == s2 else '| BERUBAH (ada job live?)', flush=True)

if gagal:
    print('BUKTI IMPOR GAGAL:', flush=True)
    for g in gagal:
        print('  -', g, flush=True)
    sys.exit(1)
print('BUKTI IMPOR LOLOS: semua modul dari /tmp/jev-opt3, sk()=True, '
      'RULE_VERSION=jev-peta-v8, 0 panggilan Jev', flush=True)
print('SELESAI')
