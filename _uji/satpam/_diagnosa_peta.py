"""Cari AKAR: kenapa [9] dan [71] petanya membengkak?

Ukur: apa isi peta yang dihasilkan mesin, dan apakah 'BAB' asli tertangkap.
"""
import glob
import os
import sys

sys.path.insert(0, '/app')
from pathlib import Path

from app.models import FileBerkas, SessionLocal
from app.ai import _teks_dari_berkas
from app.state import buang_daftar_isi, deteksi_bab_besar, deteksi_subbab, petakan

db = SessionLocal()
for fid, nama in ((9, 'TESIS_Goras'), (71, 'TESIS-unhas-manajemen')):
    f = db.query(FileBerkas).filter(FileBerkas.id == fid).first()
    p = None
    for k in glob.glob(f'/app/**/{f.nama_simpan}', recursive=True)[:5]:
        if os.path.isfile(k):
            p = Path(k); break
    teks = _teks_dari_berkas(p, f.nama or p.name) or ''
    bersih = buang_daftar_isi(teks)
    bab = deteksi_bab_besar(teks)
    sub = deteksi_subbab(teks)
    peta = petakan(teks)

    print('═' * 80)
    print(f'[{fid}] {nama}')
    print(f'   panjang teks        : {len(teks):,}')
    print(f'   setelah daftar isi  : {len(bersih):,}  (dibuang {len(teks)-len(bersih):,})')
    print(f'   deteksi_subbab      : {len(sub)} → {[b["section_id"] for b in sub[:12]]}')
    print(f'   deteksi_bab_besar   : {len(bab)} → {[b["section_id"] for b in bab]}')
    print(f'   petakan() memakai   : {len(peta)} bagian '
          f'({"sub-bab" if peta is sub else "bab besar" if len(bab) else "seluruh"})')
    print('   ← judul yang dipakai peta:')
    for b in peta[:10]:
        print(f'        {b["section_id"]:8s} {str(b["section_title"])[:50]:52s} '
              f'{b["char_count"]:>9,} kar')
    # cari kata BAB mentah di teks (apa habis dibuang daftar isi?)
    import re
    mentah = re.findall(r'^\s*BAB\s+[IVX]+\b.{0,40}', teks, re.M)[:12]
    print('   ← "BAB" MENTAH di teks (12 pertama):')
    for m in mentah:
        print(f'        {m.strip()[:70]}')
    print()
db.close()
