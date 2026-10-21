"""ULANG uji kerja latar — kali ini pakai objek Lapor yang BENAR.

Pelajaran: `kerja` WAJIB menerima objek `proses.Lapor`, BUKAN fungsi apa pun.
Uji pertama Wulan mengirim `laporan.append` → AttributeError palsu.
"""
import asyncio
import sys

sys.path.insert(0, '/app')

from app import proses as PR  # noqa: E402
from app import rute_pembimbing_ai as RPA  # noqa: E402
from app.models import CatatanPembimbing, SessionLocal  # noqa: E402
from sqlalchemy import desc  # noqa: E402

KODE = 'uji-pembimbing-ai-langsung'
BERKAS_ID, PEMAKAI, BIMBINGAN = 1, 3, 1

db = SessionLocal()
sebelum = db.query(CatatanPembimbing).order_by(
    desc(CatatanPembimbing.id)).first()
id_sebelum = sebelum.id if sebelum else 0
db.close()
print('catatan terakhir SEBELUM:', id_sebelum)
print()

kerja = RPA._kerja(BERKAS_ID, PEMAKAI, 'Wulan', BIMBINGAN)
lapor = PR.Lapor(KODE)          # ← OBJEK yang benar


async def jalan():
    return await kerja(lapor)


print('════ MENJALANKAN (objek Lapor benar) ════')
try:
    asyncio.run(jalan())
    print('✅ kerja selesai TANPA galat')
except Exception as e:
    print('❌ GAGAL:', type(e).__name__, '→', e)
    import traceback
    traceback.print_exc()

print()
print('════ STATUS PROSES ════')
try:
    print(' ', PR.ubah_tahap, '| tahap sekarang:',
          PR.tahap_kode(KODE) if hasattr(PR, 'tahap_kode') else '(fungsi tak ada)')
except Exception as e:
    print('  (info):', e)

print()
print('════ CATATAN BARU? ════')
db = SessionLocal()
try:
    baru = (db.query(CatatanPembimbing)
            .filter(CatatanPembimbing.id > id_sebelum)
            .order_by(CatatanPembimbing.id).all())
    print('baris BARU:', len(baru))
    for x in baru:
        print('  id=', x.id, '| berkas_id=', x.berkas_id,
              '| section=', repr(x.section_id)[:20],
              '| isi=', repr(str(x.isi)[:80]))
finally:
    db.close()
