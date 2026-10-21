"""UJI _posisi_dari_jev POLA RESMI COOKBOOK — naskah Asih fid=81."""
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
dt = time.time() - t0
print(f'_posisi_dari_jev -> {len(posisi)} bab  ({dt:.2f} dtk)')
for i, nama in posisi:
    print(f'   baris {i:5d}  {nama}')

print('')
print('=== TARGET (bab ASLI, terukur di naskah MENTAH) ===')
print('   baris 350 = BAB I PENDAHULUAN')
print('   baris 561 = BAB II TINJAUAN PUSTAKA')
print('   baris 735 = BAB III METODE PENELITIAN')
print('   baris 957 = BAB IV HASIL DAN PEMBAHASAN')
print('   baris 1183 = BAB V PENUTUP')
print('')
print('=== HARUS TIDAK ADA (blok sistematika 541-557) ===')
for i, nama in posisi:
    if 535 <= i <= 565:
        print(f'   ⚠️ MALAH MUNCUL: baris {i} {nama}')
