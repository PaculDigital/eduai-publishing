#!/bin/bash
# Kenapa 0 BAB terdeteksi? Lihat teks nyata di dalam docx.
docker exec eduai-app python3 -c "
import sys, zipfile, re; sys.path.insert(0,'/app')
from app.config import UPLOAD_DIR
p = UPLOAD_DIR / '5' / 'acuan_tesis.docx'
with zipfile.ZipFile(p) as z:
    xml = z.read('word/document.xml').decode('utf-8','replace')

# Paragraf demi paragraf (cara aplikasi mem-parse)
paras = re.findall(r'<w:p[ >].*?</w:p>', xml, re.S)
print('jumlah paragraf:', len(paras))
print()
print('== PARAGRAF yang mengandung BAB (30 pertama) ==')
n = 0
for para in paras:
    txt = re.sub(r'<[^>]+>', '', para)
    txt = re.sub(r'\s+', ' ', txt).strip()
    if re.search(r'\b[Bb][Aa][Bb]\b', txt):
        n += 1
        if n <= 30:
            print(f'  [{n}] {txt[:110]!r}')
print(f'  ... total {n} paragraf ber-BAB')
" 2>&1 | tail -40