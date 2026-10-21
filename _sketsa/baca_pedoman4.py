#!/usr/bin/env python3
"""CARI ATURAN PARAGRAF, MARGIN, KERTAS, PENOMORAN (26Sep26).

Bos bertanya khusus: jarak halaman ke paragraf, inden jorok,
model penomoran. Cari kalimat yang memuat itu.
"""
import re

import fitz

PDF = ('/opt/data/cache/documents/'
       'doc_0e40131213cc_PEDOMAN PENULISAN SKRIPSI PRODI MANAJEMEN EDISI REVISI 2025.pdf')
d = fitz.open(PDF)
H = [p.get_text() for p in d]
SEMUA = '\n'.join(H)

POLA = {
    'KERTAS': r'[^\n]*(kertas|HVS|kuarto|A4|folio)[^\n]*',
    'MARGIN/TEPI': r'[^\n]*(margin|batas tepi|tepi kiri|tepi atas|4 cm|3 cm|4 \(empat\))[^\n]*',
    'PARAGRAF/INDEN': r'[^\n]*(paragraf|alenia|ketukan|tab|menjorok|rata kiri kanan|indent)[^\n]*',
    'SPASI': r'[^\n]*(spasi|jarak baris|jarak antar)[^\n]*',
    'NOMOR HALAMAN': r'[^\n]*(nomor halaman|penomoran halaman|page number|letak nomor)[^\n]*',
    'PENOMORAN BAB': r'[^\n]*(penomoran bab|nomor bab|BAB I|sub.bab|anak sub)[^\n]*',
    'HURUF': r'[^\n]*([Tt]imes new [Rr]oman|jenis huruf|ukuran huruf|font)[^\n]*',
    'KUTIPAN': r'[^\n]*(kutipan|sitasi|referensi|APA)[^\n]*',
}
for judul, pola in POLA.items():
    print('=' * 78)
    print(' ', judul)
    print('=' * 78)
    hasil = re.findall(pola, SEMUA, re.I)
    # buang yang terlalu pendek / hanya nomor
    bersih = []
    for h in hasil:
        s = ' '.join(h.split())
        if len(s) > 25 and s not in bersih:
            bersih.append(s)
    for b in bersih[:12]:
        print(' •', b[:250])
    print()
