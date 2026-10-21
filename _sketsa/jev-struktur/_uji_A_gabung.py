"""POLA A: KODE GABUNG dulu (BAB + judul bawah) -> JEV nilai UNIT UTUH.
Kode cuma merapikan (tidak menilai). Jev putuskan mana bab asli.
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

# ── LANGKAH 1 (KODE): GABUNG baris judul yang terbelah jadi SATU unit ──
# Aturan kode: kalau baris pendek diikuti baris pendek (<=60) yang juga calon
# judul, dan baris pertama TIDAK diakhiri titik -> itu SATU judul yang terbelah.
def pendek_calon(b):
    return bool(b) and len(b) <= 60 and not b.endswith('.')

unit = []            # [(baris_awal, teks_unit, baris_anggota)]
i = 0
while i < len(baris):
    b = baris[i]
    if not pendek_calon(b):
        i += 1; continue
    # gabung beruntun baris pendek (maks 3)
    anggota = [i]; teks = b
    j = i + 1
    while j < len(baris) and len(anggota) < 3 and pendek_calon(baris[j]):
        # hanya gabung kalau baris berikut TIDAK punya nomor halaman di ujung
        if re.search(r'\d\s*$', baris[j]) and len(baris[j]) < 40:
            break
        teks += ' ' + baris[j]; anggota.append(j); j += 1
    unit.append((i, ' '.join(teks.split()), anggota))
    i = j if len(anggota) > 1 else i + 1

# saring unit yang mengandung penanda struktur
PENANDA = re.compile(r'\b(BAB|PENDAHULUAN|PENUTUP|KESIMPULAN|SARAN|TINJAUAN|'
                     r'PUSTAKA|METODE|HASIL|PEMBAHASAN|ABSTRAK|LAMPIRAN|'
                     r'TABEL|GAMBAR)\b', re.I)
unit = [(i, teks, ang) for i, teks, ang in unit if PENANDA.search(teks) and len(teks) <= 110]
print(f'unit (sesudah kode gabung): {len(unit)}')
for i, teks, ang in unit:
    print(f'   L{i:04d} {teks[:70]}')
