#!/usr/bin/env python3
"""UKUR ULANG sesudah perbaikan pola BAB (05Okt26, putusan Bos "A").

Membandingkan SEBELUM vs SESUDAH pada 18 naskah ASLI:
  · bab nambah di yang tadinya 0? (gunanya)
  · ada yang RUSAK/turun?       (bahayanya)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app.ai import _teks_dari_berkas                        # noqa: E402
from app.state import deteksi_bab_besar, deteksi_subbab, petakan  # noqa: E402

KEL1 = Path('/app/_contoh-dokumen/tesis-bos-gdrive')
KEL2 = Path('/app/_contoh-dokumen')
berkas = sorted(KEL1.glob('*.pdf'))
berkas += sorted(KEL2.glob('*/*.docx'))
berkas += sorted(KEL2.glob('*/*.txt'))

print('═' * 100)
print('  SESUDAH PERBAIKAN — 18 naskah ASLI')
print('═' * 100)
print(f'  {"berkas":28} {"kar":>9} {"BAB":>4} {"sub":>5}  bagian (peta)')
print('─' * 100)
tot = {'bab': 0, 'sub': 0, 'peta': 0, 'n': 0, 'gagal': []}
for p in berkas:
    try:
        t = _teks_dari_berkas(p, p.name)
    except Exception as e:                                  # noqa: BLE001
        print(f'  {p.name[:28]:28} [GALAT] {type(e).__name__}')
        continue
    if not t.strip():
        print(f'  {p.name[:28]:28} [KOSONG/tak terbaca]')
        continue
    bab = deteksi_bab_besar(t)
    sub = deteksi_subbab(t)
    pt = petakan(t)
    tot['bab'] += len(bab)
    tot['sub'] += len(sub)
    tot['peta'] += len(pt)
    tot['n'] += 1
    if not bab:
        tot['gagal'].append(p.name)
    print(f'  {p.name[:28]:28} {len(t):>9,} {len(bab):>4} {len(sub):>5}  '
          f'{len(pt)}')

print('─' * 100)
print(f'  naskah diukur : {tot["n"]}')
print(f'  total BAB     : {tot["bab"]}')
print(f'  total sub-bab : {tot["sub"]}')
print(f'  total peta    : {tot["peta"]}')
print(f'  masih BAB=0   : {len(tot["gagal"])} → {tot["gagal"]}')
print('═' * 100)
