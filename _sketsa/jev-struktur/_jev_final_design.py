"""Rancang bahan SEMPIT: baris kandidat + 1 tetangga, + pertanyaan dikelompokkan.
Ukur besar state + jumlah pertanyaan SEBELUM kirim.
"""
import sys, re
sys.path.insert(0, '/app')
import app.ai as ai_mod
from app.models import FileBerkas, SessionLocal

db = SessionLocal()
fb = db.get(FileBerkas, 81)
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '')
db.close()
baris = [' '.join(b.split()) for b in t.split('\n')]

PENANDA = re.compile(r'\b(BAB|PENDAHULUAN|PENUTUP|KESIMPULAN|SARAN|TINJAUAN|'
                     r'PUSTAKA|METODE|HASIL|PEMBAHASAN|ABSTRAK|LAMPIRAN|'
                     r'SISTEMATIKA)\b', re.I)
calon = [i for i, b in enumerate(baris) if b and len(b) <= 90 and PENANDA.search(b)]
print(f'kandidat: {len(calon)}')

# v1: kandidat saja (tanpa tetangga)
st1 = '\n'.join(f'L{i:04d}| {baris[i][:70]}' for i in calon)
print(f'\nA. kandidat saja      : {len(calon)} baris, {len(st1):,} kar, {len(calon)} tanya')

# v2: kandidat + 1 tetangga BAWAH saja (judul sering di baris bawah)
pilih = sorted({j for i in calon for j in (i, i+1) if j < len(baris) and baris[j]})
st2 = '\n'.join(f'L{j:04d}| {baris[j][:70]}' for j in pilih)
print(f'B. kandidat + 1 bawah : {len(pilih)} baris, {len(st2):,} kar, {len(calon)} tanya')

# v3: HANYA baris yang BENAR-BENAR pendek (<=40 kar) = ciri judul bab murni
pendek = [i for i in calon if len(baris[i]) <= 45]
st3 = '\n'.join(f'L{i:04d}| {baris[i][:70]}' for i in pendek)
print(f'C. kandidat <=45 kar  : {len(pendek)} baris, {len(st3):,} kar, {len(pendek)} tanya')
for i in pendek[:40]:
    print(f'      L{i:04d}| {baris[i][:60]}')
