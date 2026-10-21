#!/usr/bin/env python3
"""CARI naskah NYATA milik Bos (paling banyak tabel) di uploads.

Aturan: jangan menebak nama berkas — periksa ISI (jumlah tabel + panjang teks).
"""
import zipfile
from pathlib import Path

kandidat = []
for p in Path('/app/uploads/6').glob('*.docx'):
    try:
        with zipfile.ZipFile(p) as z:
            doc = z.read('word/document.xml').decode('utf-8', 'ignore')
        tabel = doc.count('<w:tbl>')
        teks = len(doc)
        kandidat.append((tabel, teks, p.stat().st_size, p.name))
    except Exception:                                         # noqa: BLE001
        continue

kandidat.sort(reverse=True)
print('── 8 berkas dengan tabel TERBANYAK ──')
print(f'{"tabel":>6} {"xml":>9} {"byte":>9}  nama')
for t, x, b, n in kandidat[:8]:
    print(f'{t:>6} {x:>9,} {b:>9,}  {n}')
