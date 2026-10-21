#!/usr/bin/env python3
"""SELIDIK POLA DALAM (05Okt26, putusan Bos "A").

SEBELUM mengubah _POLA_SUBBAB jadi berapa tingkat, LIHAT DULU hasil polanya
pada 89 naskah nyata: mana yang WAJAR dan mana yang MIRIP SAMPAH
(daftar tabel, nomor halaman, daftar pustaka).

Ini pencegahan "kode dulu, rusak kemudian" — persis permintaan Bos.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, '/opt/data/services/eduai-publishing')

PETA = Path('/opt/data/services/eduai-publishing/_naskah_uji_teks')

# pola berlapis: bab.anak(.cucu)(.cicit) — SEDALAM APA PUN
POLA = re.compile(
    r'^\s*([1-9]|[12]\d)((?:\.\d{1,2}){1,4})\.?\s+([A-Z][^\n]{2,110})$',
    re.MULTILINE)


def dlm(x: str) -> int:
    return len([p for p in x.strip('.').split('.') if p])


berkas = sorted(PETA.glob('*.txt'))
print('═' * 100)
print(f'  SELIDIK POLA DALAM — {len(berkas)} naskah nyata')
print('═' * 100)

kedalaman = Counter()
judul_aneh: list[tuple[str, str, str]] = []
contoh: list[str] = []
total = 0
n_palsu_kandidat = 0

POLA_PALSU = [
    (re.compile(r'\b(hlm|hal|halaman|tabel|gambar|grafik|lampiran)\b', re.I),
     'kata tabel/gambar/halaman'),
    (re.compile(r'\.{3,}|\s\d{1,3}$'), 'titik pengarah / nomor di ujung'),
    (re.compile(r'^(?:daftar|list)\b', re.I), 'kata daftar'),
]

for p in berkas:
    try:
        t = p.read_text(encoding='utf-8', errors='ignore')
    except Exception:                                         # noqa: BLE001
        continue
    for m in POLA.finditer(t):
        nomor = f'{m.group(1)}{m.group(2)}'
        judul = (m.group(3) or '').strip()
        total += 1
        kedalaman[dlm(nomor)] += 1
        for r, alasan in POLA_PALSU:
            if r.search(judul):
                n_palsu_kandidat += 1
                if len(judul_aneh) < 25:
                    judul_aneh.append((p.name[:30], nomor, f'{judul[:52]}  ← {alasan}'))
                break
        if len(contoh) < 12:
            contoh.append(f'{p.name[:26]}  {nomor:10}  {judul[:48]}')

print(f'\n  TOTAL kandidat   : {total:,}')
print(f'  TERDUGA SAMPAH   : {n_palsu_kandidat} '
      f'({100*n_palsu_kandidat/max(1,total):.1f}%)')
print('\n  ── sebaran kedalaman ──')
for d in sorted(kedalaman):
    print(f'    {d} tingkat : {kedalaman[d]:5}')

print('\n  ── contoh kandidat (paling atas) ──')
for c in contoh:
    print('    ' + c)

print('\n  ── calon SAMPAH (perlu disaring!) ──')
for nama, nomor, j in judul_aneh[:16]:
    print(f'    {nama:32} {nomor:9}  {j}')
if n_palsu_kandidat > len(judul_aneh):
    print(f'    ... dan {n_palsu_kandidat - len(judul_aneh)} lainnya')
