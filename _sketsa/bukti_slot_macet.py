"""BUKTI: antrean MACET — slot tidak dilepas saat kerja DIJALANKAN dari
LUAR `_utas` (mis. lewat `asyncio.run` langsung, atau thread tanpa finally).

DUGAAN (dari baca kode):
  `jalankan()` → `_antre_atau_jalan()` menaikkan `_sedang_jalan += 1`
  → `_utas(kode, kerja)` memasang `finally: _selesai_satu()`.

  TAPI uji Wulan tadi memanggil `_revisi_kerja` LANGSUNG (tanpa `_utas`)
  DAN `ai_revisi` lewat `asyncio.run` → slot naik, tapi TIDAK PERNAH turun.
  ⇒ Setelah 8 kali, `_sedang_jalan` mentok 8 → SEMUA permintaan masuk antrean
    → tidak pernah dijalankan karena `_selesai_satu()` tak pernah dipanggil.

UJI 2 ARAH:
  A. panggil `ai_revisi` 1× → lihat `_sedang_jalan` naik?
  B. kalau naik dan TIDAK turun setelah selesai → TERBUKTI MACET.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, '/app')

import app.ai as A                                                    # noqa: E402
from sqlalchemy import select                                         # noqa: E402
from app import proses as P                                           # noqa: E402
from app.models import (BerkasPembimbingan, CatatanPembimbing,         # noqa: E402
                        FileBerkas, PemakaianAI, SessionLocal, User)

CATATAN_ID = 106

print('═' * 74)
print('  BUKTI: SLOT ANTREAN TIDAK DILEPAS')
print('═' * 74)
print(f'SEBELUM: _sedang_jalan={P._sedang_jalan} · antrean={list(P._antrean)}')

db = SessionLocal()
k = db.execute(select(CatatanPembimbing).where(
    CatatanPembimbing.id == CATATAN_ID)).scalar_one()
pb = db.execute(select(BerkasPembimbingan).where(
    BerkasPembimbingan.id == k.berkas_id)).scalar_one()
fb = db.execute(select(FileBerkas).where(
    FileBerkas.id == pb.file_id)).scalar_one()
u = db.execute(select(User).where(User.id == fb.user_id)).scalar_one()

p = db.execute(select(PemakaianAI).where(
    PemakaianAI.user_id == u.id)).scalar_one_or_none()
if p is not None:
    p.jumlah_revisi = 0
    db.commit()


class Req:                                                                # noqa: D101
    def __init__(self, b):
        self._b = b

    async def json(self):
        return self._b


body = {'file_id': fb.id, 'bab': '__seluruh__',
        'komentar': [k.isi or 'perbaiki'], 'setuju_bagian': True}

print('\n── A. panggil ai_revisi() via asyncio.run (SEPERTI WORKER) ──')
try:
    h = asyncio.run(A.ai_revisi(Req(body), u, db))
    print(f'   hasil: kode={h.get("kode")} status={h.get("status")} '
          f'tahap={h.get("tahap")}')
except Exception as e:                                                    # noqa: BLE001
    print(f'   GAGAL: {type(e).__name__}: {str(e)[:150]}')

print(f'\n   SESUDAH: _sedang_jalan={P._sedang_jalan} '
      f'· antrean={list(P._antrean)}')
print(f'   statistik={P.statistik_antrean()}')

print('\n── B. tunggu 40 dtk, apakah slot dilepas oleh utas latar? ──')
import time                                                               # noqa: E402
for i in (10, 20, 30, 40):
    time.sleep(10)
    print(f'   t+{i:2d}s: _sedang_jalan={P._sedang_jalan} '
          f'· antrean={list(P._antrean)} · {P.statistik_antrean()}')

print('\n── C. cek DB: proses apa yg jalan/gagal? ──')
db2 = SessionLocal()
for r in db2.execute(select(
        P.ProsesAI.id, P.ProsesAI.kode, P.ProsesAI.status,
        P.ProsesAI.tahap, P.ProsesAI.galat).order_by(
        P.ProsesAI.id.desc()).limit(3)):
    print('   ', r)
