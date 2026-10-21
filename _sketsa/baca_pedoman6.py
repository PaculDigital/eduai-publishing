#!/usr/bin/env python3
"""AMBIL bagian 6.x BAHAN, UKURAN, FORMAT, PENOMORAN secara UTUH (26Sep26)."""
import re

import fitz

PDF = ('/opt/data/cache/documents/'
       'doc_0e40131213cc_PEDOMAN PENULISAN SKRIPSI PRODI MANAJEMEN EDISI REVISI 2025.pdf')
d = fitz.open(PDF)
alir = re.sub(r'\s+', ' ', ' '.join(p.get_text() for p in d))

#  mulai dari "6.2 Bahan dan Ukuran" sampai sebelum "BAB" berikutnya
i = alir.find('6.2 Bahan dan Ukuran')
if i < 0:
    i = alir.find('Bahan dan Ukuran')
print('=' * 78)
print('  BAGIAN 6 — BAHAN, UKURAN, FORMAT (utuh)')
print('=' * 78)
print(alir[i:i + 5200])
