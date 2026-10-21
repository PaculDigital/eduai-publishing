#!/bin/bash
# HITUNG ULANG CELAH setelah perbaikan deteksi bab
docker exec eduai-app python3 -c "
import sys; sys.path.insert(0,'/app')
from app.ai import _teks_dari_berkas, hitung_bagian
from app.versi import deteksi_bab
from app.config import UPLOAD_DIR, AI_POTONG_KARAKTER, KUOTA_PAKET

p = UPLOAD_DIR / '5' / 'acuan_tesis.docx'
teks = _teks_dari_berkas(p, 'acuan_tesis.docx')

print('='*72)
print('  HITUNG ULANG — tesis Bos sebagai contoh nyata')
print('='*72)
print(f'  Panjang dokumen : {len(teks):,} karakter'.replace(',','.'))
print(f'  Batas per bagian: {AI_POTONG_KARAKTER:,}'.replace(',','.'))
print()

bab = deteksi_bab(teks)
print(f'  BAB TERDETEKSI  : {len(bab)}')
print()
print('  ' + '-'*68)
print(f'  {\"Bab\":<34} {\"Karakter\":>10} {\"Bagian\":>7} {\"Kumul\":>7}')
print('  ' + '-'*68)
kum = 0; lewat = False
for b in bab:
    bg = hitung_bagian(b['isi'])
    kum += bg
    tanda = ''
    if kum > 3 and not lewat:
        tanda = '  <-- BATAS GRATIS (3)'; lewat = True
    print(f'  {b[\"label\"]+\" \"+b[\"judul\"][:27]:<34} {b[\"panjang\"]:>10,} {bg:>7} {kum:>7}{tanda}'.replace(',','.'))
print('  ' + '-'*68)
print()

n = 0; tot = 0
for b in bab:
    tot += hitung_bagian(b['isi'])
    if tot <= 3: n += 1
print(f'  >>> GRATIS (3 revisi) BISA MENYELESAIKAN: {n} BAB PERTAMA')
print()
print('='*72)
print('  PERBANDINGAN TIAP PAKET')
print('='*72)
print(f'  {\"Paket\":<12} {\"Revisi\":>7} {\"Bab terselesaikan\":>20}')
print('  ' + '-'*45)
for nama, v in KUOTA_PAKET.items():
    rev = v['revisi']
    print(f'  {nama:<12} {rev:>7} {rev:>14} bab (1 bab = 1 revisi)')
print()
print('  CATATAN: 1 bab tesis Bos (~13.000 kar) = 1 bagian = 1 revisi.')
print('           Dokumen >55.000 kar dalam SATU bab = 2+ revisi.')
print()
print('='*72)
print('  OPSI \"SELURUH DOKUMEN\" (celah yang perlu keputusan Bos)')
print('='*72)
print(f'  Seluruh tesis = {hitung_bagian(teks)} bagian = {hitung_bagian(teks)} revisi')
print(f'  Sisa kuota gratis setelah 1 klik: {3 - hitung_bagian(teks)} dari 3')
" 2>&1 | tail -45