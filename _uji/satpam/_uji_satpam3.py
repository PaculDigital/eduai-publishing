"""UJI SATPAM v3 — apakah blok prompt benar & jalur ai.py tetap aman.

Dijalankan DI DALAM container eduai-app.
"""
import glob
import os
import sys

sys.path.insert(0, '/app')
from pathlib import Path

from app import satpam
from app.ai import _teks_dari_berkas
from app.models import FileBerkas, SessionLocal
from app.state import buang_daftar_isi, petakan

GAGAL = []


def cek(nama, syarat, bukti=''):
    if syarat:
        print(f'  LULUS  {nama}  {bukti}')
    else:
        print(f'  GAGAL  {nama}  {bukti}')
        GAGAL.append(nama)


print('═' * 80)
print('  UJI SATPAM v3 — BLOK PROMPT + JALUR ai.py')
print('═' * 80)

# ── 1. blok_prompt: keputusan mati → '' (pagar: prompt tak berubah)
print('\n[1] blok_prompt saat satpam MATI → kosong')
cek('mati → ""', satpam.blok_prompt({'ok': False}, []) == '')
cek('None → ""', satpam.blok_prompt(None, []) == '')

print('\n[2] blok_prompt saat LOLOS')
b = satpam.blok_prompt({'ok': True, 'keputusan': 'lolos', 'confidence': 0.98,
                        'jumlah_bab': 5, 'jumlah_bab_mesin': 5}, [])
cek('lolos → ada isi', bool(b) and 'SUDAH DIPERIKSA' in b)
cek('lolos → tidak sebut nama AI/model', 'Jev' not in b and 'clef' not in b.lower())

b2 = satpam.blok_prompt({'ok': True, 'keputusan': 'lolos', 'confidence': 0.98,
                         'jumlah_bab': 3, 'jumlah_bab_mesin': 8}, [])
cek('jumlah beda → dijelaskan (dua-duanya sah)', 'DUA-DUANYA SAH' in b2)

print('\n[3] blok_prompt saat TANYA / TOLAK → AI diperintah jangan mengarang')
bt = satpam.blok_prompt({'ok': True, 'keputusan': 'tanya', 'confidence': 0.55,
                         'jumlah_bab': 5, 'jumlah_bab_mesin': 9}, [])
cek('tanya → perintah jangan mengarang', 'JANGAN mengarang' in bt)
bl = satpam.blok_prompt({'ok': True, 'keputusan': 'tolak', 'confidence': 0.30,
                         'jumlah_bab': None, 'jumlah_bab_mesin': 5}, [])
cek('tolak → jangan sebut nomor bab', 'jangan menyebut nomor bab' in bl.lower())

# ── 4. jalur penuh pada naskah nyata: petakan + periksa + blok
print('\n[4] jalur penuh pada 6 naskah nyata')
db = SessionLocal()
try:
    for fid, nama in ((9, 'TESIS_Goras'), (60, 'SKRIPSI-unmul'),
                      (70, 'SKRIPSI-unhas-olahraga'), (71, 'TESIS-unhas-manajemen'),
                      (72, 'DISERTASI-unhas-stunting'), (81, 'SKRIPSI-Asih')):
        f = db.query(FileBerkas).filter(FileBerkas.id == fid).first()
        p = None
        for k in glob.glob(f'/app/**/{f.nama_simpan}', recursive=True)[:5]:
            if os.path.isfile(k):
                p = Path(k); break
        teks = _teks_dari_berkas(p, f.nama or p.name) or ''
        peta = petakan(buang_daftar_isi(teks))
        h = satpam.periksa(teks, peta)
        blok = satpam.blok_prompt(h, peta)
        cek(f'[{fid}] {nama[:22]:22s} {h["keputusan"]:5s} '
            f'{h["confidence"]:.2f} → blok {len(blok):>4} kar',
            h['keputusan'] in ('lolos', 'tanya', 'tolak', 'mati')
            and isinstance(blok, str))
finally:
    db.close()

# ── 5. catat() tidak melempar galat
print('\n[5] catat() aman')
try:
    satpam.catat(None, 81, {'keputusan': 'lolos', 'confidence': 0.9,
                            'jumlah_bab': 5, 'detik': 0.4, 'alasan': 'uji'}, [])
    cek('catat() tidak melempar galat', True)
except Exception as e:
    cek('catat() tidak melempar galat', False, str(e))

print()
print('═' * 80)
if GAGAL:
    print(f'  ❌ GAGAL — {len(GAGAL)} asersi:')
    for g in GAGAL:
        print(f'     · {g}')
    sys.exit(1)
print('  ✅ SEMUA LULUS')
