#!/usr/bin/env python3
"""CARI ATURAN FORMAT — versi BENAR (26Sep26).

Pelajarannya: teks PDF TERPENGGAL PER BARIS, jadi regex '[^\n]*' tidak
bisa menangkap kalimat utuh. WAJIB gabung dulu jadi SATU baris panjang,
baru dicari konteks di sekitarnya.
"""
import re

import fitz

PDF = ('/opt/data/cache/documents/'
       'doc_0e40131213cc_PEDOMAN PENULISAN SKRIPSI PRODI MANAJEMEN EDISI REVISI 2025.pdf')
d = fitz.open(PDF)
#  gabung semua jadi satu aliran, buang pemenggalan baris
raw = ' '.join(p.get_text() for p in d)
alir = re.sub(r'\s+', ' ', raw)

KUNCI = ['kertas', 'margin', 'batas tepi', 'tepi', 'paragraf', 'alenia',
         'ketukan', 'spasi', 'nomor halaman', 'penomoran', 'Times New Roman',
         'kutipan', 'rata kiri kanan', 'menjorok']

print(f'aliran teks: {len(alir)} karakter\n')
print('=' * 78)
print('  KONTEKS SETIAP KATA KUNCI (±230 karakter)')
print('=' * 78)
for k in KUNCI:
    print(f'\n▓▓▓ {k.upper()} ▓▓▓')
    tampil = 0
    for m in re.finditer(re.escape(k), alir, re.I):
        a = max(0, m.start() - 130)
        b = min(len(alir), m.end() + 200)
        potong = alir[a:b].strip()
        if len(potong) < 40:
            continue
        print(f'  …{potong}…')
        tampil += 1
        if tampil >= 5:
            break
