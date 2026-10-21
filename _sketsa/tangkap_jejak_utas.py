"""TANGKAP JEJAK: kenapa utas worker MATI tanpa memanggil AI?

Fakta: `P.jalankan()` → status 'jalan' → 10 dtk kemudian ditutup penjaga hantu
       TANPA panggilan AI sama sekali, DAN tanpa log galat.

Uji ini memasang cangkang (hook) pada `tandai_gagal` + menangkap jejak
`traceback` langsung dari utas — supaya tahu galat aslinya.
"""
import asyncio
import sys
import threading
import time
import traceback

sys.path.insert(0, '/app')

from sqlalchemy import select                                         # noqa: E402
from app import ai as A                                               # noqa: E402
from app import proses as P                                           # noqa: E402
from app.models import (BerkasPembimbingan, CatatanPembimbing,         # noqa: E402
                        FileBerkas, PemakaianAI, ProsesAI, SessionLocal,
                        User)

JEJAK: list[str] = []
GALAT_TERTANGKAP: list[str] = []

#  ── cangkang: rekam setiap tandai_gagal ────────────────────────────────
TG_ASLI = P.tandai_gagal


def tg_sadap(kode, galat):
    GALAT_TERTANGKAP.append(f'{kode}: {galat}')
    print(f'   [SADAP tandai_gagal] {kode}: {galat[:200]}')
    return TG_ASLI(kode, galat)


P.tandai_gagal = tg_sadap

#  ── cangkang: rekam pemanggilan AI ─────────────────────────────────────
RF_ASLI = A._revisi_kerja


async def rk_sadap(*a, **kw):
    print('   [SADAP] _revisi_kerja MULAI dipanggil...')
    try:
        return await RF_ASLI(*a, **kw)
    except Exception as e:                                                # noqa: BLE001
        print(f'   [SADAP] _revisi_kerja LEMPAR: {type(e).__name__}: {e}')
        JEJAK.append(traceback.format_exc())
        raise


A._revisi_kerja = rk_sadap

db = SessionLocal()
k = db.execute(select(CatatanPembimbing).where(
    CatatanPembimbing.id == 106)).scalar_one()
pb = db.execute(select(BerkasPembimbingan).where(
    BerkasPembimbingan.id == k.berkas_id)).scalar_one()
fb = db.execute(select(FileBerkas).where(
    FileBerkas.id == pb.file_id)).scalar_one()
u = db.execute(select(User).where(User.id == fb.user_id)).scalar_one()
pem = db.execute(select(PemakaianAI).where(
    PemakaianAI.user_id == u.id)).scalar_one_or_none()
if pem is not None:
    pem.jumlah_revisi = 0
    db.commit()

print('═' * 74)
print('  TANGKAP JEJAK UTAS YANG MATI')
print('═' * 74)


class Req:                                                                # noqa: D101
    def __init__(self, b):
        self._b = b

    async def json(self):
        return self._b


body = {'file_id': fb.id, 'bab': '__seluruh__',
        'komentar': [k.isi or 'perbaiki'], 'setuju_bagian': True}


async def kerja(lapor):
    print('   [KERJA] masuk — memanggil _revisi_kerja...')
    await A._revisi_kerja(Req(body), u, db)
    print('   [KERJA] selesai normal')


p = P.mulai(db, user_id=u.id, file_id=fb.id,
            komentar=[k.isi or 'perbaiki'], jumlah_bagian=2, panjang=64243)
print(f'proses kode={p.kode}\n')
P.jalankan(p.kode, kerja)

for i in range(1, 16):
    time.sleep(6)
    db.expire_all()
    px = db.execute(select(ProsesAI).where(
        ProsesAI.kode == p.kode)).scalar_one()
    print(f'   t+{i*6:3d}s · status={px.status:<9} jalan={P._sedang_jalan} '
          f'· utas={[t.name for t in threading.enumerate() if "proses-ai" in t.name]}')
    if px.status in ('selesai', 'gagal'):
        print(f'\n   status akhir: {px.status} · galat={px.galat[:200]!r}')
        break

print(f'\n══ GALAT TERTANGKAP ({len(GALAT_TERTANGKAP)}) ══')
for g in GALAT_TERTANGKAP:
    print(' ', g[:250])

print(f'\n══ JEJAK DARI _revisi_kerja ({len(JEJAK)}) ══')
if not JEJAK:
    print('  (TIDAK ADA) — berarti _revisi_kerja TIDAK PERNAH dipanggil, '
          'atau gagal SEBELUM masuk.')
    print('  ⇒ periksa: apakah utas mati saat IMPORT atau saat BUKA DB?')
for j in JEJAK:
    print(j[:1500])
