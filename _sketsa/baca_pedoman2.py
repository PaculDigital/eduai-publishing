#!/usr/bin/env python3
"""CARI ATURAN TEKNIS PENGETIKAN di pedoman (26Sep26).

Wulan sebelumnya salah: pedoman punya BAB khusus teknis pengetikan.
Cari kata kunci yang lebih tepat: kertas, huruf, spasi, margin,
penomoran bab, dan bagian "TEKNIK PENULISAN".
"""
import re

import fitz

PDF = ('/opt/data/cache/documents/'
       'doc_0e40131213cc_PEDOMAN PENULISAN SKRIPSI PRODI MANAJEMEN EDISI REVISI 2025.pdf')
d = fitz.open(PDF)
H = [p.get_text() for p in d]

# 1. cari halaman yang memuat aturan teknis
POLA = [
    r'kertas\s+(yang\s+)?(digunakan|ukuran|HVS|A4|kuarto)',
    r'ukuran\s+kertas',
    r'huruf\s+(yang\s+)?(digunakan|Times|font)',
    r'Times\s+New\s+Roman',
    r'spasi\s+(ganda|satu|tunggal|1,5|satu\s+setengah)',
    r'jarak\s+antara\s+baris',
    r'margin',
    r'batas\s+(tepi|pengetikan|margin)',
    r'4\s*cm|3\s*cm|4\s*\(empat\)|3\s*\(tiga\)',
    r'penomoran\s+(bab|halaman|sub)',
    r'paragraf\s+baru',
    r'indent|menjorok',
    r'TEKNIK\s+PENULISAN',
]
print('=' * 78)
print('  HALAMAN PENGETIKAN TEKNIS')
print('=' * 78)
skor = {}
for i, t in enumerate(H):
    s = sum(len(re.findall(p, t, re.I)) for p in POLA)
    if s >= 2:
        skor[i + 1] = s
for hal in sorted(skor, key=lambda x: -skor[x])[:8]:
    print(f'  hal {hal}: skor {skor[hal]}')

print('\n' + '=' * 78)
print('  ISI HALAMAN TERKUAT')
print('=' * 78)
hal_kuat = sorted(skor, key=lambda x: -skor[x])[0]
print(f'\n>>> HAL {hal_kuat}:\n')
print(H[hal_kuat - 1])
