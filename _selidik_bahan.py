"""Selidik: kenapa keterbatasan/fenomena/novelty tidak masuk bahan."""
import sys

sys.path.insert(0, '/app')
from app import konversi as K                                      # noqa: E402
import app.ai as ai_mod                                            # noqa: E402
from app.models import FileBerkas, SessionLocal                    # noqa: E402

db = SessionLocal()
fb = db.get(FileBerkas, 81)
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '')
baris = t.split('\n')
p = K._cari_bab_skripsi(baris)
print('penanda:', [(i, n[:24]) for i, n in p])
print()
print('=== kata ini ada di baris berapa? ===')
for kata in ['keterbatasan', 'fenomena', 'novelty', 'kebaruan', 'celah']:
    ids = [i for i, bb in enumerate(baris) if kata in bb.lower()]
    print(f'  {kata:14} baris: {ids[:6]}  (total {len(ids)})')
print()
print('=== panjang tiap bagian ===')
for n, (i, nama) in enumerate(p):
    akhir = p[n + 1][0] if n + 1 < len(p) else len(baris)
    isi = '\n'.join(baris[i + 1:akhir]).strip()
    print(f'  {nama[:34]:36} baris {i}-{akhir} = {len(isi):,} kar')
db.close()
