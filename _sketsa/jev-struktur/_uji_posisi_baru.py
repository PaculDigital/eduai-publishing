"""UJI: _posisi_dari_jev() pola cookbook — naskah Asih fid=81."""
import sys, time
sys.path.insert(0, '/app')
from app import konversi as K
import app.ai as ai_mod
from app.models import FileBerkas, SessionLocal

db = SessionLocal()
fb = db.get(FileBerkas, 81)
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '')
db.close()
print(f'naskah: {len(t):,} kar\n')

t0 = time.time()
posisi = K._posisi_dari_jev(t)
print(f'JEV _posisi_dari_jev → {len(posisi)} bab  ({time.time()-t0:.2f} dtk)')
for i, nama in posisi:
    print(f'   L{i:04d}  {nama}')

print()
print('=== TARGET (terukur dari _cari_bab_skripsi di naskah MENTAH) ===')
print('   5 bab: baris 350 / 545 / 735 / 957 / 1183')
print()

# cek bahan mutu sekarang
t0 = time.time()
bahan = K._bahan_mutu(t)
print(f'_bahan_mutu → {len(bahan):,} kar ({time.time()-t0:.2f} dtk)')
print(bahan[:400])
print('...')
