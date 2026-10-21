"""KENAPA 0 kandidat? Cek: apakah baris pendek BERTETANGGA ada sama sekali?"""
import sys
sys.path.insert(0, '/app')
from app import konversi as K
import app.models as M
from app.models import SessionLocal
import app.ai as ai_mod
from app.state import buang_daftar_isi

db = SessionLocal()
fb = db.query(M.FileBerkas).filter(M.FileBerkas.id == 75).first()
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '') or ''
db.close()
bersih = buang_daftar_isi(t)
baris = [' '.join(x.split()) for x in bersih.split('\n')]
baris = [s for s in baris if not s.startswith(K._PENANDA_INTERNAL)]
print(f'baris: {len(baris):,}')
#  sebaran panjang
import statistics
p = [len(x) for x in baris]
print(f'panjang baris: min {min(p)} · median {int(statistics.median(p))} · max {max(p)}')
print(f'baris <= 60 kar: {sum(1 for x in p if x<=60):,}')
print(f'baris kosong   : {sum(1 for x in baris if not x):,}')
print()
#  cek pasangan: berapa kali DUA baris pendek berdampingan?
pas = 0
contoh = []
for i in range(1, len(baris)):
    a, b = baris[i-1], baris[i]
    if a and b and len(a) <= 60 and len(b) <= 60:
        pas += 1
        if len(contoh) < 10: contoh.append((i, a[:40], b[:40]))
print(f'pasangan baris <=60 kar: {pas:,}')
print()
print('── 25 baris APA SAJA (indeks 0-24) ──')
for i in range(min(25, len(baris))):
    print(f'   {i:>4} | {len(baris[i]):>4} kar | {baris[i][:64]}')
print()
print('── 25 baris di TENGAH (12000-12024) ──')
for i in range(12000, min(12025, len(baris))):
    print(f'   {i:>6} | {len(baris[i]):>4} kar | {baris[i][:64]}')
