"""CEK: apakah utas worker BENAR-BENAR jalan, atau MATI sebelum `finally`?

Fakta terukur 25Sep26:
  · `_sedang_jalan` naik 1 lalu turun ke 0 (slot dilepas) → `finally` JALAN
  · TAPI status DB tetap 'jalan' dan TIDAK ADA panggilan AI
  ⇒ utas MATI di suatu titik SEBELUM memanggil AI, dan `finally` melepas slot
    tanpa menutup status (karena `tandai_gagal` TIDAK terpanggil?).

Uji ini: jalankan kerja yang SENGAJA GAGAL + kerja SUKSES → lihat apa yang
dilakukan `_utas` pada status DB.
"""
import sys
import time
import threading

sys.path.insert(0, '/app')

from sqlalchemy import select                                         # noqa: E402
from app import proses as P                                           # noqa: E402
from app.models import ProsesAI, SessionLocal                          # noqa: E402

db = SessionLocal()

print('═' * 74)
print('  UJI: apa yang terjadi pada status DB saat kerja GAGAL/SUKSES?')
print('═' * 74)


async def kerja_gagal(lapor):
    raise RuntimeError('UJI SENGAJA GAGAL')


async def kerja_menggantung(lapor):
    import asyncio
    await asyncio.sleep(3)
    return 'selesai-normal'


#  ── UJI 1: kerja yang MELEMPAR galat ────────────────────────────────────
p1 = P.mulai(db, user_id=6, file_id=None, komentar=['uji'],
             jumlah_bagian=1, panjang=10)
print(f'\nUJI 1 (GAGAL): kode={p1.kode} status_awal={p1.status}')
P.jalankan(p1.kode, kerja_gagal)
time.sleep(6)
db.expire_all()
x = db.execute(select(ProsesAI).where(ProsesAI.kode == p1.kode)).scalar_one()
print(f'   hasil: status={x.status} tahap={x.tahap!r}')
print(f'   galat={x.galat[:160]!r}')

#  ── UJI 2: kerja normal tapi TIDAK memanggil tandai_selesai ─────────────
p2 = P.mulai(db, user_id=6, file_id=None, komentar=['uji'],
             jumlah_bagian=1, panjang=10)
print(f'\nUJI 2 (SUKSES tanpa tandai): kode={p2.kode} status_awal={p2.status}')
P.jalankan(p2.kode, kerja_menggantung)
time.sleep(8)
db.expire_all()
y = db.execute(select(ProsesAI).where(ProsesAI.kode == p2.kode)).scalar_one()
print(f'   hasil: status={y.status} tahap={y.tahap!r}')
print(f'   galat={y.galat[:160]!r}')

print(f'\nstatistik antrean: {P.statistik_antrean()}')
print(f'utas hidup: {[t.name for t in threading.enumerate() if "proses-ai" in t.name]}')
print()
print('KESIMPULAN:')
print('  · kerja GAGAL → tandai_gagal dipanggil? Lihat UJI 1.')
print('  · kerja SUKSES tanpa tandai_selesai → status tetap jalan (hantu).')
