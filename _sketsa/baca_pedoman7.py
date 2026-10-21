#!/usr/bin/env python3
"""CARI & TAMPILKAN aturan BAHAN/UKURAN/PENOMORAN lengkap (26Sep26).

Cari nomor bagian yang benar dulu, baru tampilkan isinya.
"""
import re

import fitz

PDF = ('/opt/data/cache/documents/'
       'doc_0e40131213cc_PEDOMAN PENULISAN SKRIPSI PRODI MANAJEMEN EDISI REVISI 2025.pdf')
d = fitz.open(PDF)
alir = re.sub(r'\s+', ' ', ' '.join(p.get_text() for p in d))

#  temukan semua judul bagian 6.x / 7.x
print('══ JUDUL BAGIAN (6.x & 7.x) ══')
for m in re.finditer(r'6\.\d|7\.\d', alir):
    potong = alir[m.start():m.start() + 75].strip()
    if re.match(r'^\d\.\d\s+[A-Z]', potong):
        print(' •', ' '.join(potong.split())[:70])

print()
print('=' * 78)
print('  ISI: BAHAN DAN UKURAN + FORMAT')
print('=' * 78)
for penanda in ['Bahan dan Ukuran', 'Bahan dan ukuran naskah']:
    i = alir.find(penanda)
    if i > 0:
        print(alir[i:i + 4200])
        break
