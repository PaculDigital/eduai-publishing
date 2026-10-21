"""JEV MAKSIMAL #2 — DUA TAHAP.
TAHAP 1: Jev memeta WILAYAH RINTANGAN (daftar isi / sistematika / lampiran).
TAHAP 2: baris sisa (bersih) -> Jev putuskan awal bab, dengan konteks bebas cemar.
Kode: HANYA pecah baris + beri ID. Nol regex penilai.
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

baris = [' '.join(b.split()) for b in t.split('\n')]
print(f'baris: {len(baris)}\n')

# ─────────────────────────────────────────────────────────────
# TAHAP 1: peta wilayah. Kirim SAMPLER: tiap baris ber-ID TAPI diringkas
# jadi "denah" — supaya Jev bisa menilai wilayah tanpa state raksasa.
# Denah = tiap baris asli, tapi teks dipangkas 60 kar. Baris kosong ditandai.
# ─────────────────────────────────────────────────────────────
denah = '\n'.join(
    f'{i:04d}|{b[:58]}' for i, b in enumerate(baris))
print(f'denah: {len(denah):,} kar, {len(baris)} baris')
print(denah[:300])
print('...')
