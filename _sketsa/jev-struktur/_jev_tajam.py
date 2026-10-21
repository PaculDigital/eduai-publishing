"""POLA BENAR TAJAM: kode sari KETAT -> hanya baris CALON JUDUL BAB.
Dokumentasi: 'the model gets only the questions code cannot answer from the text'
             'Pecah pertanyaan luas -> atomik'
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

# ── KODE SARI (dokumentasi: 'saring di kode dulu') ──
# Ciri JUDUL: pendek (<=90), TIDAK berakhir titik/koma kalimat, huruf kapital
# dominan ATAU mengandung kata penanda struktur. Fakta teks — bukan tebakan bentuk.
PENANDA = re.compile(r'\b(BAB|PENDAHULUAN|PENUTUP|KESIMPULAN|SARAN|TINJAUAN|'
                     r'PUSTAKA|METODE|HASIL|PEMBAHASAN|ABSTRAK|LAMPIRAN|'
                     r'SISTEMATIKA)\b', re.I)
calon = []
for i, b in enumerate(baris):
    if not b or len(b) > 90: continue
    if not PENANDA.search(b): continue
    calon.append(i)
print(f'kalon (pendek + ada penanda): {len(calon)}')
for i in calon:
    print(f'   L{i:04d}| {baris[i][:70]}')
