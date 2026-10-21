"""TANGKAP HASIL: apa yang `_revisi_kerja` KEMBALIKAN lewat jalur latar?

Fakta: lewat `P.jalankan`, `_revisi_kerja` SELESAI NORMAL tanpa galat, tapi
status DB tetap 'jalan' → penjaga hantu menutupnya jadi 'gagal'.
⇒ Berarti hasil suksesnya TIDAK PERNAH disimpan.

Uji ini menangkap NILAI BALIK `_revisi_kerja` di jalur latar + memeriksa
apakah `tandai_selesai` dipanggil.
"""
import asyncio
import json
import sys
import threading
import time

sys.path.insert(0, '/app')

from sqlalchemy import select                                         # noqa: E402
from app import ai as A                                               # noqa: E402
from app import proses as P                                           # noqa: E402
from app.models import (BerkasPembimbingan, CatatanPembimbing,         # noqa: E402
                        FileBerkas, PemakaianAI, ProsesAI, SessionLocal,
                        User)

HASIL: list = []
TANDAI: list = []

TS_ASLI = P.tandai_selesai


def ts_sadap(kode, **kw):
    TANDAI.append((kode, kw.get('model_ai'), kw.get('token_in')))
    print(f'   [SADAP tandai_selesai] kode={kode} model={kw.get("model_ai")} '
          f'token_in={kw.get("token_in")}')
    return TS_ASLI(kode, **kw)


P.tandai_selesai = ts_sadap

RK_ASLI = A._revisi_kerja


async def rk_sadap(*a, **kw):
    h = await RK_ASLI(*a, **kw)
    HASIL.append(h)
    print(f'   [SADAP] _revisi_kerja SELESAI, hasil kunci='
          f'{list(h.keys()) if isinstance(h, dict) else type(h).__name__}')
    if isinstance(h, dict):
        print(f'          ok={h.get("ok")} model={h.get("model")} '
              f'bagian={h.get("bagian")} token_revisi={h.get("token_revisi")}')
    return h


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
print('  APA YANG DIKEMBALIKAN _revisi_kerja LEWAT JALUR LATAR?')
print('═' * 74)
print(f'SEBELUM: tandai_selesai dipanggil {len(TANDAI)}x\n')


class Req:                                                                # noqa: D101
    def __init__(self, b):
        self._b = b

    async def json(self):
        return self._b


body = {'file_id': fb.id, 'bab': '__seluruh__',
        'komentar': [k.isi or 'perbaiki'], 'setuju_bagian': True}


async def kerja(lapor):
    h = await A._revisi_kerja(Req(body), u, db)
    print(f'   [KERJA] hasil balik: {type(h).__name__} · '
          f'{str(h)[:300]}')


p = P.mulai(db, user_id=u.id, file_id=fb.id,
            komentar=[k.isi or 'perbaiki'], jumlah_bagian=2, panjang=64243)
print(f'proses kode={p.kode}\n')
P.jalankan(p.kode, kerja)

for i in range(1, 16):
    time.sleep(6)
    db.expire_all()
    px = db.execute(select(ProsesAI).where(
        ProsesAI.kode == p.kode)).scalar_one()
    print(f'   t+{i*6:3d}s status={px.status} jalan={P._sedang_jalan}')
    if px.status in ('selesai', 'gagal'):
        break

print('\n══ RINGKASAN ══')
print(f'`tandai_selesai` dipanggil : {len(TANDAI)}x')
print(f'hasil _revisi_kerja dicatat: {len(HASIL)}x')
if HASIL and isinstance(HASIL[0], dict):
    print('\nISI HASIL:')
    print(json.dumps({k2: v for k2, v in HASIL[0].items()
                      if k2 != 'jawaban'}, indent=2, ensure_ascii=False)[:900])
print('\n⇒ Kalau `tandai_selesai` 0x padahal hasil ADA → '
      'PEKERJA (worker di ai.py) LUPA memanggilnya.')
