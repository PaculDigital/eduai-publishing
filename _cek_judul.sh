#!/bin/bash
# Kenapa BAB II-V hilang lagi? Lihat isi NYATA baris-barisnya
docker exec eduai-app python3 -c "
import sys; sys.path.insert(0,'/app')
from app.ai import _teks_dari_berkas
from app.config import UPLOAD_DIR
p = UPLOAD_DIR / '5' / 'acuan_tesis.docx'
teks = _teks_dari_berkas(p, 'acuan_tesis.docx')

print('== SEMUA baris yg diawali BAB/Bab (dengan nomor posisi) ==')
for i, b in enumerate(teks.split(chr(10))):
    s = b.strip()
    if s[:4] in ('BAB ','Bab '):
        print(f'  baris#{i:>3} len={len(s):>4} | {s[:100]!r}')
" 2>&1 | tail -15
echo
echo "=== Apakah judul asli ada sebagai baris TERPISAH di docx? Cek paragraf mentah ==="
docker exec eduai-app python3 -c "
import sys, zipfile; sys.path.insert(0,'/app')
from app.config import UPLOAD_DIR
from app.ai import _W
import xml.etree.ElementTree as ET
p = UPLOAD_DIR / '5' / 'acuan_tesis.docx'
with zipfile.ZipFile(p) as z:
    akar = ET.parse(z.open('word/document.xml')).getroot()
n = 0
for par in akar.iter(_W+'p'):
    t = ''.join(x.text or '' for x in par.iter(_W+'t')).strip()
    if t[:4] in ('BAB ','Bab ') or (t[:3]=='BAB' and len(t)<60):
        n += 1
        if n <= 20:
            # cek apakah judul (bold?)
            bold = any(b.get(_W+'b') is not None or b.get(_W+'val')=='1'
                       for b in par.iter(_W+'b'))
            gaya = par.find(_W+'pPr/'+_W+'pStyle')
            st = gaya.get(_W+'val') if gaya is not None else '-'
            print(f'  [{n:>2}] bold={bold} style={st:<12} {t[:70]!r}')
print(f'  ... total {n}')
"