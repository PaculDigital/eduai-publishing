#!/usr/bin/env python3
"""BACA PEDOMAN UTUH — halaman 1-60 (26Sep26, permintaan Bos).

Bos: "baca lagi panduan itu, hati hati lagi, saya mau ikuti semua
panduan itu dengan detail, karena akan jadi default app EduAi."

⇒ JANGAN pilih-pilih. Tulis SEMUA ke berkas supaya bisa dibaca berkali-kali
   tanpa memanggil AI lagi.
"""
import fitz

PDF = ('/opt/data/cache/documents/'
       'doc_0e40131213cc_PEDOMAN PENULISAN SKRIPSI PRODI MANAJEMEN EDISI REVISI 2025.pdf')
KELUAR = '/opt/data/services/eduai-publishing/_bahan/PEDOMAN_UTUH.txt'

import os
os.makedirs(os.path.dirname(KELUAR), exist_ok=True)

d = fitz.open(PDF)
with open(KELUAR, 'w') as f:
    for i, p in enumerate(d):
        f.write(f'\n{"=" * 78}\n  HALAMAN PDF {i + 1}\n{"=" * 78}\n')
        f.write(p.get_text())

print('halaman:', d.page_count)
print('ditulis ke:', KELUAR)
import subprocess
print(subprocess.run(['wc', '-l', '-c', KELUAR], capture_output=True, text=True).stdout)
