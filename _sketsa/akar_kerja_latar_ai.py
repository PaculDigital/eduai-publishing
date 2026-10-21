"""JALANKAN KERJA LATAR pembimbing-AI SECARA LANGSUNG — lihat apakah gagal.

Kenapa: lewat rute, kegagalan terjadi di dalam utas latar sehingga tidak
kelihatan di log. Di sini kita panggil fungsi kerjanya langsung dan TANGKAP
semua galat + cetak laporannya.
"""
import asyncio
import sys

sys.path.insert(0, '/app')

from app.models import SessionLocal, User  # noqa: E402
from app import rute_pembimbing_ai as RPA  # noqa: E402

BERKAS_ID = 1      # bimbingan 1, file_id 60
PEMAKAI = 3        # admin (wulan@bikinaja.me)
BIMBINGAN = 1
NAMA_MHS = 'Wulan'

print('Menyiapkan kerja latar...')
kerja = RPA._kerja(BERKAS_ID, PEMAKAI, NAMA_MHS, BIMBINGAN)
print('tipe:', type(kerja).__name__)

laporan = []


async def jalankan():
    res = kerja(laporan.append)
    if asyncio.iscoroutine(res):
        await res
    return res


print()
print('════ MENJALANKAN ════')
try:
    asyncio.run(jalankan())
    print('✅ kerja selesai TANPA galat')
except Exception as e:
    print('❌ GAGAL:', type(e).__name__, '→', e)
    import traceback
    traceback.print_exc()

print()
print('════ LAPORAN ════')
for x in laporan:
    print('  ', x)

print()
print('════ CATATAN BARU? ════')
from app.models import CatatanPembimbing  # noqa: E402
from sqlalchemy import desc  # noqa: E402

db = SessionLocal()
try:
    c = db.query(CatatanPembimbing).order_by(desc(CatatanPembimbing.id)).limit(3).all()
    for x in c:
        print('  id=', x.id, '| isi=', repr(str(x.isi)[:70]))
finally:
    db.close()
