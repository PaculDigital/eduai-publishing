"""UKUR BATAS DETEKSI STRUKTUR — 35 naskah ASLI (bukan 7).

Tujuan (tugas B): ketahui seberapa sering mesin GAGAL memetakan sub-bab,
dan APA penyebabnya. Bukan menebak — mengukur.

Jalankan DI DALAM container:
    docker exec eduai-app python3 /app/_ukur_batas_struktur.py
"""
import glob
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, '/app')

from app.ai import _teks_dari_berkas          # noqa: E402
from app.models import FileBerkas, SessionLocal  # noqa: E402
from app.state import (buang_daftar_isi, deteksi_bab_besar,  # noqa: E402
                       deteksi_subbab)

# pola PEMBANDING (bukan untuk produksi — hanya mengukur apa yang DILEWATKAN)
POLA_VARIAN = {
    'X.Y biasa        ': re.compile(r'^\s*([1-9]|[12]\d)\.(\d{1,2})\.?\s+([A-Z][^\n]{2,110})$', re.M),
    'X.Y.Z tiga tingkat': re.compile(r'^\s*([1-9]|[12]\d)\.\d{1,2}\.(\d{1,2})\.?\s+([A-Z][^\n]{2,110})$', re.M),
    'A. huruf         ': re.compile(r'^\s*([A-Z])\.(\d?)\.?\s+([A-Z][^\n]{3,110})$', re.M),
    'BAB romawi       ': re.compile(r'^\s*(?i:BAB)\s+([IVXLC]{1,5})\b', re.M),
    'BAB angka arab   ': re.compile(r'^\s*(?i:BAB)\s+(\d{1,2})\b', re.M),
    'Bagian/Bagian ke ': re.compile(r'^\s*(?i:bagian)\s+(?:ke-?\s*)?(\d{1,2}|[IVX]+)\b', re.M),
}

db = SessionLocal()
print('═' * 100)
print('  UKUR BATAS DETEKSI STRUKTUR — SELURUH NASKAH ASLI')
print('═' * 100)
print(f'{"id":>3} {"kar":>9} {"sub":>4} {"bab":>4} | {"X.Y":>4} {"XYZ":>4} {"A.":>4} '
      f'{"BABr":>5} {"BABa":>5} {"Bgn":>4} | sebab')

baris_hasil = []
for f in db.query(FileBerkas).all():
    nama = f.nama or ''
    p = None
    for k in glob.glob(f'/app/**/{f.nama_simpan}', recursive=True)[:5]:
        if os.path.isfile(k):
            p = Path(k)
            break
    if not p:
        continue
    try:
        t = _teks_dari_berkas(p, nama) or ''
    except Exception:                                        # noqa: BLE001
        continue
    if len(t) < 500:
        continue
    tb = buang_daftar_isi(t)
    sub = len(deteksi_subbab(t))
    bab = len(deteksi_bab_besar(t))
    n = {k: len(v.findall(tb)) for k, v in POLA_VARIAN.items()}

    # SEBAB: mengapa sub-bab 0 / sedikit?
    sebab = '-'
    if sub == 0:
        if n['X.Y biasa        '] == 0 and n['X.Y.Z tiga tingkat'] > 0:
            sebab = 'HANYA X.Y.Z (pola butuh X.Y)'
        elif n['X.Y biasa        '] == 0 and n['A. huruf         '] > 0:
            sebab = f"HANYA huruf A. ({n['A. huruf         ']} buah)"
        elif n['X.Y biasa        '] == 0 and n['BAB angka arab   '] > 0:
            sebab = 'BAB angka arab'
        elif n['X.Y biasa        '] == 0:
            sebab = 'MEMANG TAK BERNOMOR'
        else:
            sebab = f"saring palsu? ({n['X.Y biasa        ']} kandidat ditolak)"
    baris_hasil.append((f.id, len(t), sub, bab, n, sebab, nama))
    print(f'{f.id:>3} {len(t):>9,} {sub:>4} {bab:>4} | '
          f'{n["X.Y biasa        "]:>4} {n["X.Y.Z tiga tingkat"]:>4} '
          f'{n["A. huruf         "]:>4} {n["BAB romawi       "]:>5} '
          f'{n["BAB angka arab   "]:>5} {n["Bagian/Bagian ke "]:>4} | {sebab}')

print()
print('═' * 100)
naskah = len(baris_hasil)
n0 = sum(1 for b in baris_hasil if b[2] == 0)
n_kurang = sum(1 for b in baris_hasil if b[2] < 3)
print(f'RINGKASAN: {naskah} naskah diukur')
print(f'  sub-bab = 0   : {n0} ({100*n0/max(naskah,1):.0f}%)  → HARGA jatuh ke BAB BESAR')
print(f'  sub-bab < 3   : {n_kurang} ({100*n_kurang/max(naskah,1):.0f}%)  → dianggap tidak layak sub-bab')
print()
print('PENYEBAB (yang bisa ditolong):')
from collections import Counter
for s, c in Counter(b[5] for b in baris_hasil if b[2] == 0).most_common():
    print(f'  {c:>2}× {s}')
db.close()
