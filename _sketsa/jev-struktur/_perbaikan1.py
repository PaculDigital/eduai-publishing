"""Perbaikan 1: BUANG daftar isi pakai state.buang_daftar_isi() sebelum pecah."""
import sys, re
sys.path.insert(0, '/app')
from app import konversi as K
from app.state import buang_daftar_isi
import app.ai as ai_mod
from app.models import FileBerkas, SessionLocal

db = SessionLocal()
fb = db.get(FileBerkas, 81)
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '')
db.close()
print(f'naskah: {len(t):,} kar')

bersih = buang_daftar_isi(t)
print(f'sesudah buang_daftar_isi: {len(bersih):,} kar  ({len(bersih)/len(t)*100:.0f}%)')

blok = K._pecah_blok(bersih)
jenis = K._klasifikasi_blok(blok)
print(f'blok: {len(blok)}')
print()
print('=== heading yg mengandung "BAB" ===')
for n, b in enumerate(blok):
    if jenis.get(n) == 'heading' and re.search(r'\bBAB\b', b['text'], re.I):
        print(f'  B{n:03d} baris {b["lines"][0]}  {b["text"][:60]}')
print()
print('=== "Sistematika" ===')
for n, b in enumerate(blok):
    if re.search(r'sistematika', b['text'], re.I):
        print(f'  B{n:03d} [{jenis.get(n)}] {b["text"][:80]}')
