#!/usr/bin/env python3
"""SELIDIK 3 MASALAH pada 11 tesis Bos (05Okt26, putusan Bos "A").

#1 teks mentok 200.000 kar  → SUDAH terjawab: batas `[:200_000]` di ai.py
#2 BAB besar = 0 padahal ada sub-bab (290462754, 290465463)
#3 sub-bab = 0 padahal ada BAB (290460818, 389360758)

Tujuan: BUKTI dari naskahnya sendiri — penomoran aslinya bagaimana.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app.ai import _teks_dari_berkas                        # noqa: E402
from app.state import buang_daftar_isi, deteksi_bab_besar, deteksi_subbab  # noqa: E402

KEL = Path('/app/_contoh-dokumen/tesis-bos-gdrive')

#  #2 BAB=0      #3 sub-bab=0
SOROT = ['290462754.pdf', '290465463.pdf', '290460818.pdf', '389360758.pdf']

for nama in SOROT:
    p = KEL / nama
    if not p.exists():
        print(f'[hilang] {nama}')
        continue
    t = _teks_dari_berkas(p, nama)
    bersih = buang_daftar_isi(t)
    bab = deteksi_bab_besar(t)
    sub = deteksi_subbab(t)

    print('═' * 92)
    print(f'  {nama}   {len(t):,} kar')
    print(f'  BAB={len(bab)}  sub-bab={len(sub)}')
    print('─' * 92)

    # apa yang ditulis naskahnya? cari SEMUA bentuk penomoran bagian
    uji = [
        (r'BAB\s+[IVXLC]{1,5}', 'BAB romawi'),
        (r'BAB\s+\d{1,2}', 'BAB angka arab'),
        (r'^\s*([IVXLC]{1,5})\.\s+[A-Z]', 'romawi titik (I.)'),
        (r'^\s*([A-Z])\.\s+[A-Z][a-z]', 'huruf titik (A.)'),
        (r'^\s*(\d{1,2})\.\s+[A-Z][a-z]', 'angka titik (1.)'),
        (r'^\s*(\d{1,2})\.(\d{1,2})\b', 'dua tingkat (1.1)'),
        (r'^\s*(\d{1,2})\.(\d{1,2})\.(\d{1,2})\b', 'tiga tingkat (1.1.1)'),
        (r'^\s*(\d{1,2})\)\s+[A-Z]', 'angka tutup (1))'),
        (r'^\s*([a-z])\.\s+[A-Za-z]', 'huruf kecil (a.)'),
    ]
    for pola, label in uji:
        n = len(re.findall(pola, bersih, re.MULTILINE))
        if n:
            print(f'    {label:24} : {n}')

    print()
    print('    ── contoh 5 baris yang MIRIP judul bagian ──')
    n = 0
    for m in re.finditer(r'^.{0,3}([A-Z][^\n]{4,70})$', bersih, re.MULTILINE):
        bar = m.group(1).strip()
        if (re.match(r'^(BAB|[IVXLC]{1,5}\.\s|\d{1,2}[\.\)]\s|[A-Z]\.\s)', bar)
                and len(bar) < 60):
            print(f'      | {bar}')
            n += 1
            if n >= 5:
                break
    print()
