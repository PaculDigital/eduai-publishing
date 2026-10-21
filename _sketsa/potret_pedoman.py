#!/usr/bin/env python3
"""POTRET halaman pedoman jadi GAMBAR supaya bisa DILIHAT MATA (26Sep26).

Bos: "Lihat juga pakai vision bentuknya kan ada contohnya."
⇒ Tabel 2 (teknik penulisan) & lampiran contoh sampul/judul itu BENTUK.
   Teks saja tidak cukup — WAJIB dilihat.
"""
import os

import fitz

PDF = ('/opt/data/cache/documents/'
       'doc_0e40131213cc_PEDOMAN PENULISAN SKRIPSI PRODI MANAJEMEN EDISI REVISI 2025.pdf')
KELUAR = '/opt/data/services/eduai-publishing/_potret/pedoman'
os.makedirs(KELUAR, exist_ok=True)

d = fitz.open(PDF)
# halaman penting: Tabel 1 (hal 3), Tabel 2 mulai hal 39-42, lampiran contoh 53+
HAL = [3, 39, 40, 41, 42, 43, 44, 53, 54, 56, 57, 58, 59, 60, 61]
for h in HAL:
    if h < 1 or h > d.page_count:
        continue
    p = d[h - 1]
    pix = p.get_pixmap(dpi=110)
    nama = f'{KELUAR}/hal-{h:03d}.png'
    pix.save(nama)
    print(f'hal {h:3d} → {nama}  ({os.path.getsize(nama) // 1024} KB)')
