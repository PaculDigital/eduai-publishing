"""KENAPA 5 dari 6 catatan TIDAK KETEMU di naskah?

Catatan uji Wulan: "Latar belakang belum menunjukkan kesenjangan penelitian."
Naskah proposal Bos punya kalimat mirip. Kenapa gagal?
"""
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app import ai as AI
from app import cari_bagian as CB

teks = AI._teks_dari_berkas(Path('/app/_uji_doc/proposal_v1_original.docx'),
                            'p.docx')

CATATAN = [
    ('Latar belakang belum menunjukkan kesenjangan penelitian.', 'BAB I'),
    ('Tambahkan data terbaru untuk mendukung argumen.', 'BAB I'),
    ('Teori utama belum disebut sama sekali.', 'BAB II'),
    ('Metode sampling belum dijelaskan.', 'BAB III'),
    ('Rencana analisis data masih terlalu umum.', 'BAB IV'),
]

print('═' * 74)
print('  KENAPA TIDAK KETEMU?')
print('═' * 74)
for c, bab in CATATAN:
    kandidat = CB._potongan_khas(c)
    hasil = CB.cari_bagian(teks, c)
    print()
    print(f'  CATATAN: {c}')
    print(f'     kandidat: {kandidat[:6]}')
    if hasil:
        print(f'     KETEMU  : dasar={hasil["dasar"]!r}')
    else:
        print('     TIDAK KETEMU')
        #  uji tiap kandidat satu-satu untuk tahu yang mana gagal
        for k in kandidat[:6]:
            pos = CB._cari_lentur(teks, k)
            print(f'        {k!r:34s} → {"ADA" if pos is not None else "tidak ada di naskah"}')
