#!/bin/bash
# BAB I 43.839 kar & BAB II 393 kar = mencurigakan. Cek posisinya.
docker exec eduai-app python3 -c "
import sys; sys.path.insert(0,'/app')
from app.ai import _teks_dari_berkas
from app.versi import deteksi_bab
from app.config import UPLOAD_DIR

p = UPLOAD_DIR / '5' / 'acuan_tesis.docx'
teks = _teks_dari_berkas(p, 'acuan_tesis.docx')
bab = deteksi_bab(teks)

print('== POSISI tiap bab ==')
for b in bab:
    print(f'  {b[\"label\"]:<8} posisi={b[\"posisi\"]:>7}  akhir={b[\"akhir\"]:>7}  panjang={b[\"panjang\"]:>7,}'.replace(',','.'))
print()
print('== AWAL isi BAB I (120 kar) ==')
b1 = bab[0]
print('  ', repr(b1['isi'][:120]))
print()
print('== AWAL isi BAB II (120 kar) ==')
b2 = bab[1]
print('  ', repr(b2['isi'][:120]))
print()
print('== AKHIR isi BAB I (150 kar) ==')
print('  ', repr(b1['isi'][-150:]))
" 2>&1 | tail -20