#!/usr/bin/env python3
"""SELIDIK POLA DALAM — SETELAH buang_daftar_isi (05Okt26).

Putaran-1 membuktikan: 93% kandidat pola-dalam adalah DAFTAR ISI. Sekarang
ukur ULANG setelah daftar isi dibuang — supaya yang dibaca = kandidat
SUNGGUHAN (judul bagian di dalam isi naskah).
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, '/opt/data/services/eduai-publishing')
import app.state as S                                      # noqa: E402

PETA = Path('/opt/data/services/eduai-publishing/_naskah_uji_teks')
POLA = re.compile(
    r'^\s*([1-9]|[12]\d)((?:\.\d{1,2}){1,4})\.?\s+([A-Z][^\n]{2,110})$',
    re.MULTILINE)


def dlm(x: str) -> int:
    return len([p for p in x.strip('.').split('.') if p])


berkas = sorted(PETA.glob('*.txt'))
print('═' * 92)
print(f'  SELIDIK SETELAH buang_daftar_isi — {len(berkas)} naskah')
print('═' * 92)

ked = Counter()
palsu: list[str] = []
contoh: list[str] = []
total = n_palsu = 0

POLA_PALSU = [
    (re.compile(r'\.{3,}'), 'titik pengarah'),
    (re.compile(r'^\s*\d{1,3}\s*$'), 'hanya angka'),
    (re.compile(r'\b(hlm|hal|halaman)\b', re.I), 'kata halaman'),
    (re.compile(r'^(daftar|list|tabel|gambar)\b', re.I), 'kata daftar/tabel'),
]

for p in berkas:
    t = S.buang_daftar_isi(p.read_text(encoding='utf-8', errors='ignore'))
    for m in POLA.finditer(t):
        nomor = f'{m.group(1)}{m.group(2)}'
        judul = (m.group(3) or '').strip()
        total += 1
        ked[dlm(nomor)] += 1
        ada_palsu = False
        for r, alasan in POLA_PALSU:
            if r.search(judul):
                n_palsu += 1
                ada_palsu = True
                if len(palsu) < 14:
                    palsu.append(f'{p.name[:28]:30} {nomor:9} {judul[:40]} ← {alasan}')
                break
        if not ada_palsu and len(contoh) < 10:
            contoh.append(f'{p.name[:28]:30} {nomor:9} {judul[:44]}')

print(f'\n  TOTAL kandidat        : {total}')
print(f'  TERDUGA SAMPAH        : {n_palsu} ({100*n_palsu/max(1,total):.1f}%)')
print('  ── sebaran kedalaman ──')
for d in sorted(ked):
    print(f'    {d} tingkat : {ked[d]:5}')
print('\n  ── CONTOH kandidat BERSIH ──')
for c in contoh:
    print('    ' + c)
print('\n  ── calon SAMPAH sisa ──')
for x in palsu:
    print('    ' + x)
