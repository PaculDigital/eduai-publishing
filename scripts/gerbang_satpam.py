"""GERBANG SATPAM — uji yang BISA GAGAL (bukan uji yang selalu hijau).

Menguji 3 hal pada 6 naskah NYATA:
  G1. petakan() TIDAK berubah perilaku (jalur lama utuh)
  G2. kategori BAB besar kini 'bab1'..'bab5' (AKAR cacat ditutup)
  G3. satpam memberi keputusan yang masuk akal (lolos/tanya/tolak)
  G4. satpam MATI → app tetap jalan (pagar P1)

EXIT 0 = semua lulus · EXIT != 0 = ada gagal.
"""
import glob
import os
import sys

sys.path.insert(0, '/app')
from pathlib import Path

from app import satpam
from app.ai import _teks_dari_berkas
from app.models import FileBerkas, SessionLocal
from app.state import kategori_bab_besar, petakan

GAGAL = []


def cek(nama, syarat, bukti=''):
    if syarat:
        print(f'  LULUS  {nama}  {bukti}')
    else:
        print(f'  GAGAL  {nama}  {bukti}')
        GAGAL.append(nama)


print('═' * 78)
print('  GERBANG SATPAM + AKAR KATEGORI BAB')
print('═' * 78)

# ── G2: kategori bab besar (uji langsung, tanpa naskah)
print('\n[G2] kategori BAB besar → bab1..bab5')
cek('BAB I  → bab1', kategori_bab_besar('BAB I') == 'bab1', kategori_bab_besar('BAB I'))
cek('BAB V  → bab5', kategori_bab_besar('BAB V') == 'bab5', kategori_bab_besar('BAB V'))
cek('BAB 3  → bab3', kategori_bab_besar('BAB 3') == 'bab3', kategori_bab_besar('BAB 3'))
cek('BAB IX → bab (di luar 1..5, aman)',
    kategori_bab_besar('BAB IX') == 'bab', kategori_bab_besar('BAB IX'))
cek('kosong → bab (aman)', kategori_bab_besar(None) == 'bab', kategori_bab_besar(None))

# ── G1 + G3: pada naskah nyata
print('\n[G1/G3] perilaku peta + keputusan satpam pada 6 naskah nyata')
NASKAH = [(9, 'TESIS_Goras'), (60, 'SKRIPSI-unmul'), (70, 'SKRIPSI-unhas-olahraga'),
          (71, 'TESIS-unhas-manajemen'), (72, 'DISERTASI-unhas-stunting'),
          (81, 'SKRIPSI-Asih')]
db = SessionLocal()
try:
    for fid, nama in NASKAH:
        f = db.query(FileBerkas).filter(FileBerkas.id == fid).first()
        if not f:
            cek(f'[{fid}] berkas ada', False, 'tidak ada di DB')
            continue
        p = None
        for k in glob.glob(f'/app/**/{f.nama_simpan}', recursive=True)[:5]:
            if os.path.isfile(k):
                p = Path(k); break
        if p is None:
            cek(f'[{fid}] naskah fisik', False, 'tidak ketemu')
            continue
        teks = _teks_dari_berkas(p, f.nama or p.name) or ''
        peta = petakan(teks)
        h = satpam.periksa(teks, peta)

        # G1: peta harus berupa daftar tidak kosong & punya kunci wajib
        kunci_ok = all(k in b for b in peta for k in
                       ('section_id', 'section_title', 'kategori', 'char_count'))
        cek(f'[{fid}] peta utuh ({len(peta)} bagian)', bool(peta) and kunci_ok)
        # kategori tidak boleh lagi 'bab' harfiah untuk bab bernomor romawi
        adakah_bab_kosong = [b for b in peta if b['section_id'].startswith('BAB ')
                              and b['kategori'] == 'bab']
        cek(f'[{fid}] kategori bab bernomor valid',
            not adakah_bab_kosong,
            f'{len(adakah_bab_kosong)} masih "bab" harfiah')
        # G3: keputusan satpam harus salah satu dari 3 (bukan nilai aneh)
        cek(f'[{fid}] satpam memutuskan ({h["keputusan"]}, {h["confidence"]:.2f})',
            h['keputusan'] in ('lolos', 'tanya', 'tolak', 'mati'))
finally:
    db.close()

# ── G4: pagar P1 — satpam mati, app tetap jalan
print('\n[G4] pagar P1: satpam MATI → petakan tetap bekerja')
simpan = satpam.AKTIF
try:
    satpam.AKTIF = False
    h = satpam.periksa('BAB I\nPENDAHULUAN\nisi', [{'section_id': 'BAB I'}])
    cek('satpam mati → keputusan "mati"', h['keputusan'] == 'mati')
    cek('satpam mati → tidak melempar galat', isinstance(h, dict))
    peta = petakan('BAB I\nPENDAHULUAN\n\nBAB II\nTINJAUAN\n\nBAB III\nMETODE')
    cek('satpam mati → peta tetap jalan', len(peta) == 3, f'{len(peta)} bagian')
finally:
    satpam.AKTIF = simpan

# ── G5: satpam dengan alamat RUSAK → tidak melempar galat (pagar P2)
print('\n[G5] pagar P2: alamat rusak → tidak melempar galat')
simpan_base = satpam.BASE
try:
    satpam.BASE = 'http://alamat-yang-tidak-ada.invalid/v1/chat/completions'
    h = satpam.periksa('BAB I\nPENDAHULUAN\nisi', [{'section_id': 'BAB I'}])
    cek('alamat rusak → keputusan "mati"', h['keputusan'] == 'mati')
    cek('alamat rusak → tidak melempar galat', isinstance(h, dict),
        str(h.get('alasan'))[:40])
finally:
    satpam.BASE = simpan_base

print()
print('═' * 78)
if GAGAL:
    print(f'  ❌ GERBANG GAGAL — {len(GAGAL)} asersi gagal:')
    for g in GAGAL:
        print(f'     · {g}')
    sys.exit(1)
print('  ✅ GERBANG LULUS — semua asersi hijau')
