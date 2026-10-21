"""Buktikan utas latar pembersih sesi BENAR-BENAR bekerja.

FK sesi_edit → users+files: pakai USER & FILE sungguhan yang sudah ada
(user 3 admin / file 58 miliknya) lalu hapus kembali. Bukan data
produksi yang rusak — sesi uji dihapus di akhir.
"""
import sys
from datetime import datetime, timedelta, timezone

from app.models import SessionLocal, SesiEdit
from app.sesi import bersihkan_basi

db = SessionLocal()

# 1. Suntik sesi basi buatan (FK sah: user 3, file 58)
lama = datetime.now(timezone.utc) - timedelta(minutes=99)
s = SesiEdit(user_id=3, file_id=58, kunci_oo='uji-basi-27sep',
             terakhir_aktif=lama, dibuka=lama)
db.add(s)
db.commit()
print('sesi palsu disuntik, id =', s.id)

# 2. Jalankan pembersih (fungsi yang dipanggil utas latar)
jumlah = bersihkan_basi(db)
print('dibersihkan:', jumlah)

# 3. Buktikan sesi palsu HILANG
sisa = db.query(SesiEdit).filter(SesiEdit.kunci_oo == 'uji-basi-27sep').count()
print('sisa sesi palsu:', sisa)
db.close()
assert sisa == 0, 'PEMBERSIH GAGAL — sesi basi masih ada!'
print('PEMBERSIH SESI LATAR TERBUKTI BEKERJA ✅')
