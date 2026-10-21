"""SIAPKAN TOKEN UJI — bikin token tinjau BARU untuk bimbingan 1.

⚠️ Ini MENYENTUH DB produksi (kolom token_sidik). Karena itu:
  · HANYA untuk bimbingan uji (id 1),
  · CADANGAN baris lama dicetak dulu supaya bisa dikembalikan,
  · token lama tetap disimpan di berkas (bisa dipasang ulang).
"""
import sys

sys.path.insert(0, '/app')
from app.models import SessionLocal, Pembimbingan

db = SessionLocal()
b = db.query(Pembimbingan).filter(Pembimbingan.id == 1).one()

print('=== KEADAAN SEBELUM ===')
print('id:', b.id, '| nama:', b.nama, '| token_sidik:', b.token_sidik)
print('dibuat:', b.dibuat, '| kedaluwarsa:', getattr(b, 'kedaluwarsa', '-'))

#  Cetak agar bisa dipulihkan
with open('/tmp/token_lama_bimbingan1.txt', 'w') as f:
    f.write(f'{b.token_sidik}\n')
print('token_sidik lama disimpan ke /tmp/token_lama_bimbingan1.txt')
db.close()
