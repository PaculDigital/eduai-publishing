"""UJI KUNCI BERLAKU — apakah `_kunci_berlaku()` benar-benar bergigi?

Dipakai data NYATA dari DB: bimbingan 1 (Fazri, berkas id 1).
Diuji:
  A. bimbingan sah + berkas sah        → True
  B. berkas MILIK bimbingan lain       → False  (scoped, kunci tak bocor)
  C. berkas tidak ada (99999)          → False
  D. bimbingan tidak ada (99999)       → False
  E. bimbingan DICABUT                 → False  (pakai salinan, jangan rusak data)
  F. bimbingan KEDALUWARSA             → False  (idem)
"""
import sys

sys.path.insert(0, '/app')
from app.main import _kunci_berlaku                               # noqa: E402
from app.models import (BerkasPembimbingan, Pembimbingan,         # noqa: E402
                        SessionLocal)

LULUS = GAGAL = 0


def cek(nama, syarat):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}')


db = SessionLocal()

bk1 = db.query(BerkasPembimbingan).filter(
    BerkasPembimbingan.pembimbingan_id == 1).first()
print('berkas uji:', bk1.id if bk1 else None,
      '| milik bimbingan', bk1.pembimbingan_id if bk1 else None)

print('=== A. SAH ===')
cek('A1 bimbingan 1 + berkasnya → True',
    _kunci_berlaku(db, 1, bk1.id) is True)

print('=== B. SCOPED — kunci naskah lain DITOLAK ===')
lain = db.query(BerkasPembimbingan).filter(
    BerkasPembimbingan.pembimbingan_id != 1).first()
if lain:
    cek(f'B1 berkas {lain.id} (milik bimbingan {lain.pembimbingan_id}) '
        f'dibuka dengan kunci bimbingan 1 → False',
        _kunci_berlaku(db, 1, lain.id) is False)
else:
    print('  (lewati — belum ada bimbingan lain)')

print('=== C/D. YANG TIDAK ADA ===')
cek('C1 berkas 99999 → False', _kunci_berlaku(db, 1, 99999) is False)
cek('D1 bimbingan 99999 → False', _kunci_berlaku(db, 99999, bk1.id) is False)

print('=== E. DICABUT → False (pakai salinan memori, DB TIDAK diubah) ===')
b = db.query(Pembimbingan).filter(Pembimbingan.id == 1).one()
ingat = b.dicabut
b.dicabut = 1
db.flush()
cek('E1 bimbingan dicabut → False', _kunci_berlaku(db, 1, bk1.id) is False)
db.rollback()          # pulihkan
b2 = db.query(Pembimbingan).filter(Pembimbingan.id == 1).one()
cek('E2 data pulih (dicabut kembali semula)', b2.dicabut == ingat)

print('=== F. KEDALUWARSA → False (pakai salinan memori) ===')
from datetime import timedelta                                   # noqa: E402
b = db.query(Pembimbingan).filter(Pembimbingan.id == 1).one()
ingat_exp = b.kedaluwarsa
b.kedaluwarsa = ingat_exp - timedelta(days=30)
db.flush()
cek('F1 bimbingan kedaluwarsa → False', _kunci_berlaku(db, 1, bk1.id) is False)
db.rollback()
b3 = db.query(Pembimbingan).filter(Pembimbingan.id == 1).one()
cek('F2 data pulih (kedaluwarsa kembali semula)',
    b3.kedaluwarsa == ingat_exp)

print('=== G. BONUS: kunci_tinjau + _kunci_berlaku BERSAMA ===')
from app import kunci_tinjau as KT                               # noqa: E402
k = KT.kunci_untuk(1, bk1.id, KT.batas_exp(b3.kedaluwarsa))
baca = KT.baca_kunci(k)
cek('G1 kunci dibuat dari baris nyata → terbaca', baca == (1, bk1.id))
cek('G2 _kunci_berlaku menerima (1, berkas) hasil baca kunci',
    baca is not None and _kunci_berlaku(db, baca[0], baca[1]) is True)

db.close()
print()
print(f'═══ {LULUS} LULUS / {GAGAL} GAGAL ═══')
sys.exit(1 if GAGAL else 0)
