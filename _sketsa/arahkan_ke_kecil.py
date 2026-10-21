"""UJI ARAH: apakah skeleton disebabkan UKURAN naskah?

Cara: berkas uji bimbingan 1 (bk id=1) diarahkan ke naskah KECIL lebih dulu,
potret. Kalau tampil penuh → akarnya ukuran (5,3 MB), bukan kode.
Kalau tetap skeleton → akarnya bukan ukuran.

⚠️ Menyentuh kolom file_id di DB → catat nilai lama untuk dipulihkan.
"""
import sys

sys.path.insert(0, '/app')
from app.models import SessionLocal, BerkasPembimbingan, FileBerkas

db = SessionLocal()
bk = db.query(BerkasPembimbingan).filter(BerkasPembimbingan.id == 1).one()
print('SEBELUM: bk.id=1 file_id =', bk.file_id)

with open('/tmp/file_id_lama.txt', 'w') as f:
    f.write(str(bk.file_id))
print('file_id lama disimpan: /tmp/file_id_lama.txt')

#  Pakai naskah KECIL (id 51 — 0,01 MB)
kecil = db.query(FileBerkas).filter(FileBerkas.id == 51).one()
bk.file_id = kecil.id
db.commit()
print('SESUDAH: bk.id=1 file_id =', bk.file_id, f'({kecil.nama})')
db.close()
