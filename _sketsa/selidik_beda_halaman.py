"""KENAPA modul bilang KETEMU 4, tapi HALAMAN hanya pasang 1 tombol?

Selidik: lihat isi catatan yang TERSIMPAN di DB + apa yang dibaca halaman.
"""
import sys

sys.path.insert(0, '/app')
from app import cari_bagian as CB
from app import pembimbing as P
from app.models import (BerkasPembimbingan, CatatanPembimbing, Pembimbingan,
                        SessionLocal, init_db)

init_db()
db = SessionLocal()

b = db.query(Pembimbingan).filter(
    Pembimbingan.nama == 'Prof. Uji Presisi').first()
print('  bimbingan id:', b.id if b else None)

bks = P.daftar_berkas(db, b.id)
print('  berkas:', [(x.id, x.judul) for x in bks])

cat = P.daftar_catatan(db, b.id)
print('  jumlah catatan:', len(cat))
for c in cat:
    print(f'   id={c.id} berkas_id={c.berkas_id} section={c.section_id!r}')
    print(f'      isi={c.isi[:70]!r}')

print()
print('  ── uji cari_bagian untuk SETIAP catatan di DB ──')
from app.rute_pembimbing import _isi_naskah
for bk in bks:
    naskah = _isi_naskah(db, bk)
    print(f'  naskah berkas {bk.id}: {len(naskah)} kar')
    for c in cat:
        r = CB.cari_bagian(naskah, c.isi or '', c.teks_asli or '')
        print(f'   catatan {c.id}: {"KETEMU "+r["dasar"] if r else "TIDAK"}')
db.close()
