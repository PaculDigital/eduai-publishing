"""POLA BENAR (dokumentasi resmi):
 - Kode SARI dulu: buang paragraf panjang, tabulasi, isi kuesioner
 - Kode BERI ID baris
 - Kirim HANYA baris pendek (calon judul) + tetangga 2 baris -> state KECIL
 - Jev jawab noul SEMPIT per baris (satu properti per pertanyaan)
"""
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

# ── SARI DI KODE (kelemahan #5: "saring di kode dulu") ──
# Buang: baris kosong, paragraf panjang (>200 kar), baris penuh angka/tabulasi.
def calon_judul(b):
    if not b: return False
    if len(b) > 200: return False                        # paragraf, bukan judul
    if len(re.findall(r'[0-9|]', b)) > len(b) * 0.35: return False  # tabulasi/angka
    return True

idx = [i for i, b in enumerate(baris) if calon_judul(b)]
print(f'baris total {len(baris)} -> calon judul {len(idx)}')

# Kirim: hanya baris calon + 2 tetangga (yang juga calon) -> state kecil
pilih = sorted({j for i in idx for j in range(max(0,i-2), min(len(baris),i+3))
                if baris[j] and len(baris[j])<=200})
state = '\n'.join(f'L{i:04d}| {baris[i][:90]}' for i in pilih)
print(f'state: {len(pilih)} baris, {len(state):,} kar\n')
if len(state) > 40000:
    print('!! state masih besar, pangkas'); sys.exit(1)

# ── JEV: satu pertanyaan SEMPIT per baris CALON (bukan semua) ──
q = {}
for i in idx:
    q[f'b{i:04d}'] = {
        'instructions': (f'Apakah baris L{i:04d} adalah JUDUL AWAL sebuah bab '
                         f'atau bagian utama naskah akademik yang uraiannya '
                         f'panjang sesudahnya — bukan baris di dalam daftar '
                         f'isi, bukan di dalam daftar ringkasan/sistematika '
                         f'penulisan, bukan kepala tabel/gambar?'),
        'type': 'noul'}
print(f'pertanyaan: {len(q)}')
t0=time.time(); jawab = satpam.tanya_bebas_mutu(state, q) or {}
print(f'Jev: {time.time()-t0:.2f} dtk, jawaban: {len(jawab)}\n')

lolos = []
for i in idx:
    n = (jawab.get(f'b{i:04d}') or {}).get('noul')
    if n is not None and float(n) >= 0.6:
        lolos.append((i, float(n)))
print('=== LOLOS (noul>=0.6) ===')
for i, n in lolos:
    print(f'   L{i:04d} noul={n}  {baris[i][:60]}')
