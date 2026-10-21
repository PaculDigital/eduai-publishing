"""PASANG TOKEN UJI — hitung sidik dari token pilihan, SIMPAN sidik lama.

Kenapa begini: token asli disimpan HANYA sebagai sidik (satu arah) — jadi
token lama tidak bisa dipulihkan. Cara paling aman untuk menguji:
  · pilih token uji yang bentuknya SAH (lewat P.buat_token()),
  · hitung sidiknya, pasang ke bimbingan uji (id 1),
  · dicatat & dibalik ke sidik lama setelah uji.
"""
import sys

sys.path.insert(0, '/app')
from app import pembimbing as P
from app.models import SessionLocal, Pembimbingan

db = SessionLocal()
b = db.query(Pembimbingan).filter(Pembimbingan.id == 1).one()

lama = b.token_sidik
token_uji = P.buat_token()
sidik_baru = P.sidik_token(token_uji)

b.token_sidik = sidik_baru
db.commit()

print('=== DIPASANG ===')
print('token uji :', token_uji)
print('sidik baru:', sidik_baru[:24], '...')
print('sidik lama:', lama[:24], '...')
print()
print('SIMPAN untuk dipulihkan:')
with open('/tmp/pulihkan_token.txt', 'w') as f:
    f.write(f'{lama}\n{token_uji}\n')
print('  /tmp/pulihkan_token.txt')

#  Buktikan token ini benar-benar SAH lewat mesin pencari yang sama
b2, sebab = P.cari_dari_token(db, token_uji)
print()
print('=== UJI MESIN PENCARI ===')
print('cari_dari_token →', 'KETEMU bimbingan id ' + str(b2.id) if b2 else f'GAGAL ({sebab})')
db.close()
