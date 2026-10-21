#!/usr/bin/env python3
"""BACA UTUH bagian teknik pengetikan (hal 38-45) — 26Sep26.

JANGAN dipotong: tabel aturan format bisa terpenggal antar halaman.
"""
import fitz

PDF = ('/opt/data/cache/documents/'
       'doc_0e40131213cc_PEDOMAN PENULISAN SKRIPSI PRODI MANAJEMEN EDISI REVISI 2025.pdf')
d = fitz.open(PDF)
for i in range(37, 45):
    print('=' * 78)
    print(f'  HALAMAN {i + 1}')
    print('=' * 78)
    print(d[i].get_text())
