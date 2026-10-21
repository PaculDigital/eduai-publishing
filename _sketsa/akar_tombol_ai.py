"""AKAR: kenapa blok {% if ai_aktif and bk.file_id %} tidak cetak tombol?

Uji langsung dengan data NYATA: bangun konteks seperti rute_pembimbing lakukan,
lalu cetak template dengan Jinja — lihat apa yang keluar.

Ini bukan menebak: kita MENJALANKAN render yang sama di dalam container.
"""
import sys

sys.path.insert(0, '/app')

from app.models import SessionLocal, Pembimbingan, BerkasPembimbingan
from app import pembimbing

db = SessionLocal()
b = db.query(Pembimbingan).filter(Pembimbingan.id == 1).one()

print('A. Data DB:')
print('   pembimbingan id =', b.id, '| user_id =', b.user_id)

#  Pakai fungsi cari_dari_token yang SAMA dipakai rute
dari_token = None
try:
    dari_token = pembimbing.cari_dari_token(db, b.token_sidik)
    print('   cari_dari_token →', 'KETEMU' if dari_token[0] else 'TIDAK KETEMU',
          '| sebab:', dari_token[1] if len(dari_token) > 1 else '-')
except Exception as e:
    print('   cari_dari_token GALAT:', type(e).__name__, e)

#  Ambil berkas persis seperti rute
try:
    from app.rute_pembimbing import _berkas_bimbingan  # type: ignore
    bk = _berkas_bimbingan(db, b.id)
    print('B. _berkas_bimbingan →', len(bk), 'baris')
except Exception as e:
    print('B. _berkas_bimbingan tidak ada / galat:', type(e).__name__, e)
    bk = db.query(BerkasPembimbingan).filter(
        BerkasPembimbingan.pembimbingan_id == b.id).all()
    print('   fallback query →', len(bk), 'baris')

for x in bk:
    print('   id=', x.id, '| file_id=', repr(x.file_id),
          '| judul=', repr(getattr(x, 'judul', ''))[:40])

print()
print('C. Syarat template: ai_aktif and bk.file_id')
from app import pembimbing_ai as PAI
ai_aktif = PAI.aktif()
print('   ai_aktif =', ai_aktif)
for x in bk:
    print('   bk.id=', x.id, '→ bool(bk.file_id) =', bool(x.file_id),
          '→ SYARAT =', bool(ai_aktif and x.file_id))

db.close()
