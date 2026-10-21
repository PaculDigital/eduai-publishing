"""KENAPA `petunjuk` selalu kosong di halaman?

Modul bilang 3 KETEMU, tapi halaman dapat 0. Lihat kunci `simpul['id']`.
"""
import sys

sys.path.insert(0, '/app')
from app import cari_bagian as CB
from app import pembimbing as P
from app.models import Pembimbingan, SessionLocal, init_db
from app.rute_pembimbing import _isi_naskah

init_db()
db = SessionLocal()
b = db.query(Pembimbingan).filter(
    Pembimbingan.nama == 'Prof. Uji Presisi').first()

rantai = P.rangkai(P.daftar_catatan(db, b.id))
print('  jumlah simpul rantai:', len(rantai))
print()
for i, s in enumerate(rantai):
    print(f'  simpul ke-{i+1}:')
    print(f'     KUNCI di simpul : {list(s.keys())}')
    print(f"     s.get('id')     : {s.get('id')!r}   ← INI yang dipakai halaman")
    t = s.get('terbaru')
    print(f"     terbaru.id      : {getattr(t, 'id', None)!r}")
    print(f"     terbaru.isi     : {(getattr(t, 'isi', '') or '')[:50]!r}")
    print()

print('  ⚠️ halaman memakai: petunjuk[simpul.get(\'id\')]')
print('     kalau simpul.get(\'id\') = None untuk SEMUA, maka petunjuk selalu')
print('     kosong → semua catatan tampil "Tidak ditemukan".')
db.close()
