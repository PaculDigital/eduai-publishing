"""UJI dengan bahan SEMPIT 74 baris / 2.441 kar, 74 pertanyaan noul ATOMIK."""
import sys, time, re, json
sys.path.insert(0, '/app')
from app import satpam
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
pendek = [i for i, b in enumerate(baris)
          if b and len(b) <= 45 and PENANDA.search(b)]
state = '\n'.join(f'L{i:04d}| {baris[i]}' for i in pendek)
print(f'state: {len(pendek)} baris, {len(state):,} kar')

q = {f'b{i:04d}': {
      'instructions': (f'Apakah baris L{i:04d} menandai AWAL sebuah bagian '
                       f'PANJANG naskah akademik (bab/bagian berisi), BUKAN '
                       f'baris di dalam daftar isi, BUKAN daftar ringkasan, '
                       f'BUKAN judul tabel/gambar?'),
      'type': 'noul'} for i in pendek}

t0=time.time(); jawab = satpam.tanya_bebas_mutu(state, q) or {}
print(f'Jev: {time.time()-t0:.2f} dtk, jawaban: {len(jawab)}/{len(q)}\n')

TARGET = {350, 561, 735, 957, 1183}   # bab ASLI (terukur)
print(f'{"":4} {"noul":>6}  {"benar?":7} baris')
for i in pendek:
    n = (jawab.get(f'b{i:04d}') or {}).get('noul')
    lolos = n is not None and float(n) >= 0.6
    tanda = ''
    if i in TARGET:
        tanda = '✅ HIT' if lolos else '❌ LEWAT'
    elif lolos:
        tanda = '⚠️ palsu lolos'
    print(f'  L{i:04d} {str(n):>6}  {tanda:14} {baris[i][:52]}')
