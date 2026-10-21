"""Selidik cacat: kenapa 'Sistematika Penulisan' tak terdeteksi + daftar isi lolos."""
import sys, re
sys.path.insert(0, '/app')
from app import konversi as K
import app.ai as ai_mod
from app.models import FileBerkas, SessionLocal

db = SessionLocal()
fb = db.get(FileBerkas, 81)
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '')
db.close()

blok = K._pecah_blok(t)
print(f'blok: {len(blok)}')
jenis = K._klasifikasi_blok(blok)
print(f'jenis: {len(jenis)}')
print()
print('=== 40 blok pertama (dengan jenis) ===')
for n in range(min(60, len(blok))):
    b = blok[n]
    print(f'  B{n:03d} [{str(jenis.get(n)):14}] baris {b["lines"][:2]}  {b["text"][:58]}')
print()
print('=== cari "Sistematika" ===')
for n, b in enumerate(blok):
    if re.search(r'sistematika', b['text'], re.I):
        print(f'  B{n:03d} [{jenis.get(n)}] len={len(b["text"])} {b["text"][:100]}')
print()
print('=== cari heading yg mengandung "BAB" (cek wilayah) ===')
for n, b in enumerate(blok):
    if jenis.get(n) == 'heading' and re.match(r'\s*BAB\b', b['text'], re.I):
        print(f'  B{n:03d} baris {b["lines"][:2]} {b["text"][:60]}')
