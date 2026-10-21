#!/bin/bash
# BUKTI: kenapa BAB II-V hilang? + hitung celah dengan angka NYATA
docker exec eduai-app python3 -c "
import sys; sys.path.insert(0,'/app')
from app.ai import _teks_dari_berkas, hitung_bagian
from app.versi import deteksi_bab
from app.config import UPLOAD_DIR, AI_POTONG_KARAKTER

p = UPLOAD_DIR / '5' / 'acuan_tesis.docx'
teks = _teks_dari_berkas(p, 'acuan_tesis.docx')

print('='*70)
print('  BUKTI CELAH 1: judul bab II-V MENEMPEL ke kalimat penjelas')
print('='*70)
for baris in teks.split(chr(10)):
    b = baris.strip()
    if b[:4] in ('BAB ','Bab '):
        print(f'  panjang={len(b):>5} | {b[:95]!r}')
print()
print('  ^ Baris >45 kar & ada \". \" → DISARING sebagai kalimat (baris 122 versi.py)')
print('    Akibat: judul bab II-V yang sebenarnya ikut terbuang.')
print()

print('='*70)
print('  ANGKA NYATA (setelah deteksi apa adanya)')
print('='*70)
bab = deteksi_bab(teks)
print(f'  Bab terdeteksi : {len(bab)}')
for b in bab:
    print(f'    - {b[\"label\"]} : {b[\"panjang\"]:,} kar = {hitung_bagian(b[\"isi\"])} bagian'.replace(',','.'))
print()
print(f'  Panjang TOTAL dokumen : {len(teks):,} kar'.replace(',','.'))
print(f'  Batas per bagian      : {AI_POTONG_KARAKTER:,} kar'.replace(',','.'))
print(f'  SELURUH dokumen       : {hitung_bagian(teks)} bagian (= revisi)'.replace(',','.'))
print()
print('='*70)
print('  CELAH PAKET GRATIS (kuota 3 revisi)')
print('='*70)
tot = hitung_bagian(teks)
print(f'  Kalau user pilih \"seluruh dokumen\": {tot} revisi → sisa {3-tot} (DARI 3)')
print(f'  → Menghabiskan {(tot/3*100):.0f}% kuota gratis untuk SATU klik.')
print()
# simulasi kalau bab terdeteksi lengkap
print('  Kalau bab terdeteksi LENGKAP (perkiraan 5 bab @ ~13.000 kar):')
sisa = len(teks); per = sisa // 5
for i in range(1, 6):
    print(f'    BAB {i}: ~{per:,} kar = 1 bagian → total {i} revisi'.replace(',','.'))
print()
print('  → Gratis (3) BISA menyelesaikan 3 BAB dari 5.')
print('  → Tapi karena bab tak terdeteksi, user memakai 2 revisi untuk SELURUH tesis.')
" 2>&1 | tail -45