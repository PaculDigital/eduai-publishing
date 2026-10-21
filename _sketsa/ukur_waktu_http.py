"""PENGUKUR WAKTU JALUR HTTP SUNGGUHAN — antrean vs AI.

PERTANYAAN BOS 25Sep26: E2E lewat HTTP + worker gagal 420-460 dtk
dengan token_in=0. Habis di mana? ANTREAN atau AI?

CARA: bungkus 3 titik dengan pencatat waktu
  A. `proses_mod.jalankan`  → kapan utas dimulai (atau masuk antrean)
  B. `_revisi_kerja`        → kapan benar-benar mulai & selesai
  C. httpx.post             → tiap panggilan AI nyata

Lalu jalankan LEWAT ENDPOINT HTTP SUNGGUHAN (httpx ke localhost:8000),
persis seperti mahasiswa menekan tombol.
"""
import asyncio
import json
import sys
import threading
import time

sys.path.insert(0, '/app')

import httpx                                                          # noqa: E402
from sqlalchemy import select                                         # noqa: E402
from app import ai as A                                               # noqa: E402
from app import proses as P                                           # noqa: E402
from app.auth import buat_token                                       # noqa: E402
from app.models import (BerkasPembimbingan, CatatanPembimbing,         # noqa: E402
                        FileBerkas, PemakaianAI, ProsesAI, SessionLocal,
                        User)

T0 = time.time()
CATATAN: list = []


def catat(label, isi=''):
    CATATAN.append((time.time() - T0, label, isi))
    print(f'   t+{time.time()-T0:7.2f}s · {label} {isi}')


#  ── sadap A: jalankan (kapan utas mulai / antre) ───────────────────────
J_ASLI = P.jalankan


def j_sadap(kode, kerja):
    langsung = P._sedang_jalan < P.KONKUREN_MAKS
    catat('P.jalankan()', f'kode={kode} langsung={langsung} '
                          f'sedang_jalan={P._sedang_jalan}')
    return J_ASLI(kode, kerja)


P.jalankan = j_sadap

#  ── sadap B: _revisi_kerja (kapan benar-benar mulai) ───────────────────
RK_ASLI = A._revisi_kerja


async def rk_sadap(*a, **kw):
    catat('_revisi_kerja MULAI', f'di utas={threading.current_thread().name}')
    try:
        h = await RK_ASLI(*a, **kw)
        catat('_revisi_kerja SELESAI', f'ok={h.get("ok")} '
                                       f'model={h.get("model")}')
        return h
    except Exception as e:                                                # noqa: BLE001
        catat('_revisi_kerja LEMPAR', f'{type(e).__name__}: {str(e)[:100]}')
        raise


A._revisi_kerja = rk_sadap

#  ── sadap C: tiap panggilan AI ────────────────────────────────────────
POST_ASLI = httpx.AsyncClient.post


async def post_sadap(self, url, *a, **kw):
    u = str(url)
    if 'chat/completions' not in u:
        return await POST_ASLI(self, url, *a, **kw)
    t = time.time()
    catat('→ AI KIRIM', f'{u[:60]}')
    try:
        r = await POST_ASLI(self, url, *a, **kw)
        catat('← AI BALAS', f'HTTP {r.status_code} dalam {time.time()-t:.1f}s')
        return r
    except Exception as e:                                                # noqa: BLE001
        catat('← AI GAGAL', f'{type(e).__name__} setelah {time.time()-t:.1f}s')
        raise


httpx.AsyncClient.post = post_sadap

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

print('═' * 78)
print('  PENGUKUR WAKTU JALUR HTTP SUNGGUHAN')
print('═' * 78)
print(f'user={u.id} berkas={fb.id} kuota direset=0')
print(f'antrean awal: {P.statistik_antrean()}\n')

token = buat_token(u.id)
print(f'token dibuat, panjang={len(token)}\n')

BODY = {'file_id': fb.id, 'bab': '__seluruh__',
        'komentar': [k.isi or 'perbaiki'], 'setuju_bagian': True}


async def panggil_http():
    """Panggil ENDPOINT HTTP SUNGGUHAN seperti mahasiswa menekan tombol."""
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.post('http://localhost:8000/api/ai/v1/revisi',
                         json=BODY,
                         headers={'Cookie': f'eduai_session={token}'})
        return r


catat('MULAI: tekan tombol (HTTP POST)')
try:
    r = asyncio.run(panggil_http())
    catat('HTTP BALAS', f'status={r.status_code} body={r.text[:200]}')
    try:
        hasil = r.json()
    except Exception:                                                     # noqa: BLE001
        hasil = {}
except Exception as e:                                                    # noqa: BLE001
    catat('HTTP GAGAL', f'{type(e).__name__}: {str(e)[:150]}')
    hasil = {}

kode = hasil.get('kode', '')
print(f'\n   kode proses = {kode!r}')

#  ── pantau sampai selesai ─────────────────────────────────────────────
if kode:
    db2 = SessionLocal()
    for i in range(1, 46):
        time.sleep(10)
        db2.expire_all()
        px = db2.execute(select(ProsesAI).where(
            ProsesAI.kode == kode)).scalar_one_or_none()
        if px is None:
            continue
        print(f'   t+{time.time()-T0:7.1f}s · status={px.status:<9} '
              f'tahap={px.tahap[:40]:<40} · jalan={P._sedang_jalan}')
        if px.status in ('selesai', 'gagal'):
            print(f'\n   >>> AKHIR: {px.status.upper()} · '
                  f'model={px.model_ai} · token_in={px.token_in} · '
                  f'galat={(px.galat or "-")[:150]}')
            break

print('\n' + '═' * 78)
print('  URUTAN WAKTU LENGKAP')
print('═' * 78)
for t, label, isi in CATATAN:
    print(f'  t+{t:7.2f}s · {label:<22} {isi}')
print('═' * 78)
