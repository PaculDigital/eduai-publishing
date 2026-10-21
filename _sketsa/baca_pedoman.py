#!/usr/bin/env python3
"""BACA PEDOMAN PENULISAN SKRIPSI — cari aturan FORMAT (26Sep26).

Yang dicari (sesuai Bos): margin, kertas, spasi, inden jorok paragraf,
model penomoran, font, penomoran halaman, posisi judul BAB.
"""
import re

import fitz

PDF = ('/opt/data/cache/documents/'
       'doc_0e40131213cc_PEDOMAN PENULISAN SKRIPSI PRODI MANAJEMEN EDISI REVISI 2025.pdf')
d = fitz.open(PDF)
halaman = [p.get_text() for p in d]

KATA = ['margin', 'tepi', 'jarak', 'spasi', 'baris', 'indent', 'menjorok',
        'menjorok', 'paragraf', 'kertas', 'ukuran', 'font', 'huruf', 'jenis huruf',
        'times', 'nomor halaman', 'penomoran', 'kutipan', 'alinea', 'halaman']

print('=' * 78)
print('  BAGIAN YANG MEMBAHAS FORMAT — per halaman')
print('=' * 78)
hit = []
for i, t in enumerate(halaman):
    tl = t.lower()
    jumlah = sum(tl.count(k) for k in KATA)
    if jumlah >= 3:
        hit.append((i + 1, jumlah))

for hal, n in hit:
    print(f'\n── hal {hal} (kuat: {n}) ──')
    print(halaman[hal - 1].strip()[:900])

print('\n' + '=' * 78)
print('  DAFTAR ISI / bagian awal')
print('=' * 78)
print(halaman[1].strip()[:1200] if len(halaman) > 1 else '')
