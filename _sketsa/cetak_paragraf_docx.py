#!/usr/bin/env python3
"""CETAK bentuk paragraf .docx NYATA — untuk menaruh gambar TEPAT di posisi.

Aturan Bos: "CETAK DULU bentuk kunci mesin sebelum menulis kode sambungan."
Yang dicetak:
   1. Struktur <w:p> — berapa paragraf, mana yang jadi judul sub-bab?
   2. Apakah texsnya bisa dilacak dari kalimat naskah ke paragraf?
"""
import re
import sys
import zipfile
from pathlib import Path

F = Path('/app/uploads/6/349508cb13697288.docx')
with zipfile.ZipFile(F) as z:
    doc = z.read('word/document.xml').decode('utf-8')

pars = re.findall(r'<w:p\b.*?</w:p>|<w:p\b[^>]*/>', doc, re.S)
print(f'══ jumlah <w:p>: {len(pars)} ══')
print()

print('── 40 paragraf pertama (teks + penanda penting) ──')
for i, p in enumerate(pars[:40]):
    teks = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p))
    gaya = re.search(r'<w:pStyle w:val="([^"]+)"', p)
    ada_gbr = '<w:drawing' in p
    ada_tbl = '<w:tbl' in p
    tanda = []
    if gaya:
        tanda.append(f'style={gaya.group(1)}')
    if ada_gbr:
        tanda.append('GAMBAR')
    if ada_tbl:
        tanda.append('TABEL')
    if '<w:br' in p:
        tanda.append('BR')
    print(f'  {i:>3}| {teks[:66]!r:<70} {" ".join(tanda)}')

print()
print('── gaya paragraf yang DIPAKAI (semua) ──')
gaya_semua = {}
for p in pars:
    g = re.search(r'<w:pStyle w:val="([^"]+)"', p)
    k = g.group(1) if g else '(tanpa gaya)'
    gaya_semua[k] = gaya_semua.get(k, 0) + 1
for k, v in sorted(gaya_semua.items(), key=lambda x: -x[1]):
    print(f'  {v:>5} × {k}')

print()
print('── cari paragraf yang memuat judul sub-bab (2.1 / 2.2 / 2.3) ──')
for i, p in enumerate(pars):
    teks = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p))
    if re.match(r'^\s*2\.\d\s', teks.strip()) and len(teks.strip()) < 80:
        g = re.search(r'<w:pStyle w:val="([^"]+)"', p)
        print(f'  {i:>3}| {teks.strip()[:60]!r}  style={g.group(1) if g else "-"}')
