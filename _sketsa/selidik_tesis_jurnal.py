"""SELIDIK 2: apakah di TESIS LENGKAP (bukan proposal) hasilnya sudah benar?

Kalau ya → berarti masalahnya di NASKAH PROPOSAL (belum selesai), bukan kode.
Kalau tidak → berarti kode Wulan yang kurang presisi.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, '/app')

from app import ai as AI
from app import state

for nama, jalur in [
    ('TESIS S2 (sastra novel)', '/app/_uji_doc/tesis_s2.docx'),
    ('ARTIKEL JURNAL (Fransiskha)', '/app/_uji_doc/artikel_jurnal.docx'),
]:
    teks = AI._teks_dari_berkas(Path(jalur), Path(jalur).name)
    print('═' * 74)
    print(f'  {nama}')
    print('═' * 74)
    print(f'  panjang: {len(teks):,} kar')
    print()
    print('  ── semua kemunculan "BAB" (baris AWAL saja) ──')
    for m in re.finditer(r'(?im)^[ \t]*BAB[ \t]+[IVXLC0-9]{1,5}[ \t]*(.*)$', teks):
        print(f'    @{m.start():>6}  {m.group(0)!r}')
    print()
    print('  ── apa yang dibaca deteksi_bab_besar() ──')
    for i, b in enumerate(state.deteksi_bab_besar(teks), 1):
        print(f'    {i}. {b.get("section_title")!r}')
    print()
    print('  ── apakah ada judul bagian TANPA kata BAB? (artikel jurnal) ──')
    for kata in ('PENDAHULUAN', 'METODE', 'HASIL', 'KESIMPULAN', 'PEMBAHASAN',
                 'TINJAUAN PUSTAKA', 'LITERATURE'):
        n = len(re.findall(kata, teks, re.I))
        if n:
            print(f'    {kata:20s} {n}x')
    print()
