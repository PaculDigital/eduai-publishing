"""JE V MAKSIMAL #1: kirim baris ber-ID + TETANGGA (blok keadaan), Jev pilih baris awal.
TANPA regex. Kode hanya: pecah baris + beri ID + ambil blok sekitar baris ber-'BAB'.
"""
import sys, time, re
sys.path.insert(0, '/app')
from app import satpam
import app.ai as ai_mod
from app.models import FileBerkas, SessionLocal

db = SessionLocal()
fb = db.get(FileBerkas, 81)
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '')
db.close()

# KODE hanya: pecah baris + ID. TIDAK menilai, TIDAK menyaring pola bentuk.
semua = [' '.join(b.split()) for b in t.split('\n')]
print(f'total baris: {len(semua)}')

# Ambil blok: tiap baris yang mengandung "BAB" (ini PENANDA HALUS, bukan vonis)
# + 3 baris sebelum & 3 sesudah. Kode tak bilang mana bab asli.
idx = [i for i, b in enumerate(semua) if re.search(r'\bBAB\b', b, re.I) and len(b) <= 120]
print(f'baris berpendar BAB: {len(idx)}')

# rakit blok ber-ID (tetangga disertakan) — unik & urut
pilih = set()
for i in idx:
    for j in range(max(0, i-3), min(len(semua), i+4)):
        pilih.add(j)
pilih = sorted(pilih)
print(f'baris dikirim (dengan tetangga): {len(pilih)}')

state = '\n'.join(f'L{i:04d}| {semua[i][:100]}' for i in pilih if semua[i])
print(f'panjang state: {len(state):,} kar')

# Pertanyaan: Jev yang MEMUTUSKAN mana awal bab asli.
q = {}
for i in idx:
    q[f'awal_{i:04d}'] = {
        'instructions': (
            f'Baris L{i:04d} adalah "{semua[i][:60]}". Perhatikan SELURUH '
            f'keadaan di atas: apakah baris L{i:04d} ini JUDUL AWAL sebuah BAB '
            f'yang benar-benar berisi uraian panjang — BUKAN baris di dalam '
            f'daftar isi, BUKAN baris di dalam blok ringkasan/sistematika '
            f'penulisan yang memuat judul banyak bab beruntun rapat?'),
        'type': 'noul',
    }
t0 = time.time()
jawab = satpam.tanya_bebas_mutu(state, q) or {}
dt = time.time() - t0
print(f'\nJev: {dt:.2f} dtk, {len(q)} pertanyaan\n')
for i in idx:
    n = (jawab.get(f'awal_{i:04d}') or {}).get('noul')
    tanda = '✅' if (n is not None and float(n) >= 0.6) else '  '
    print(f'  {tanda} L{i:04d} noul={n}  {semua[i][:56]}')
