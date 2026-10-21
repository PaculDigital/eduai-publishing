#!/bin/bash
# LACAK: kenapa 0 bab? Pakai FUNGSI ASLI aplikasi (bukan regex ulangan)
docker exec eduai-app python3 -c "
import sys; sys.path.insert(0,'/app')
from app.ai import _teks_dari_berkas
from app.versi import deteksi_bab, _POLA_BAB
from app.config import UPLOAD_DIR
from pathlib import Path

p = UPLOAD_DIR / '5' / 'acuan_tesis.docx'
teks = _teks_dari_berkas(p, 'acuan_tesis.docx')
print('== TEKS dari parser ASLI aplikasi ==')
print('  panjang :', len(teks))
print('  ada \\\\n :', teks.count(chr(10)), 'baris')
print()
print('  == 12 baris pertama ==')
for i, b in enumerate(teks.split(chr(10))[:12], 1):
    print(f'   [{i}] {b[:90]!r}')
print()
m = list(_POLA_BAB.finditer(teks))
print('  cocok _POLA_BAB :', len(m))
for x in m[:12]:
    print(f'    pre={x.group(1)!r} angka={x.group(2)!r} judul={(x.group(3) or \"\")[:50]!r}')
print()
hasil = deteksi_bab(teks)
print('  == hasil deteksi_bab :', len(hasil), 'bab ==')
for b in hasil:
    print('    -', b['label'], '|', b['panjang'], 'kar |', b['judul'][:40])
" 2>&1 | tail -40