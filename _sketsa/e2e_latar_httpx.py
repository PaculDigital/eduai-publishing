"""E2E JALUR LATAR BELAKANG SUNGGUHAN — log httpx terbuka + waktu per tahap.

PERTANYAAN BOS 25Sep26: uji LANGSUNG selalu sukses 15-47 dtk, tapi jalur
LATAR BELAKANG gagal 420-460 dtk dgn token_in=0. Di mana bedanya?

CARA: panggil `app.ai.ai_revisi(...)` SUNGGUHAN (endpoint yang dipakai worker),
dengan PENYADAP httpx dipasang. Cetak tiap panggilan keluar + waktu.

⚠️ DB: kuota user dikembalikan otomatis oleh app kalau gagal.
   Uji ini bisa memotong kuota → reset dulu sebelum jalan.
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, '/app')

import httpx                                                          # noqa: E402
import app.ai as A                                                    # noqa: E402
from sqlalchemy import select                                         # noqa: E402
from app.models import (CatatanPembimbing, FileBerkas,                 # noqa: E402
                        BerkasPembimbingan, PemakaianAI, SessionLocal, User)

CATATAN_ID = 106
PANGGILAN: list[dict] = []
POST_ASLI = httpx.AsyncClient.post


async def post_sadap(self, url, *a, **kw):
    isi = kw.get('json') or {}
    t0 = time.time()
    baris = {'url': str(url), 'model': isi.get('model', '?'),
             'kar': len(str(isi.get('messages') or '')),
             'mulai': t0, 'status': 'jalan', 'detik': 0.0, 'awal': ''}
    PANGGILAN.append(baris)
    try:
        r = await POST_ASLI(self, url, *a, **kw)
        baris.update(status=f'HTTP {r.status_code}',
                     detik=round(time.time() - t0, 1),
                     awal=(r.text or '')[:130].replace('\n', ' '))
        return r
    except Exception as e:                                                # noqa: BLE001
        baris.update(status=f'EXC {type(e).__name__}',
                     detik=round(time.time() - t0, 1), awal=str(e)[:130])
        raise


httpx.AsyncClient.post = post_sadap

print('═' * 78)
print('  E2E JALUR LATAR BELAKANG — log httpx + waktu')
print('═' * 78)

db = SessionLocal()
k = db.execute(select(CatatanPembimbing).where(
    CatatanPembimbing.id == CATATAN_ID)).scalar_one_or_none()
pb = db.execute(select(BerkasPembimbingan).where(
    BerkasPembimbingan.id == k.berkas_id)).scalar_one_or_none()
fb = db.execute(select(FileBerkas).where(
    FileBerkas.id == pb.file_id)).scalar_one_or_none()
u = db.execute(select(User).where(User.id == fb.user_id)).scalar_one()

#  reset kuota uji
p = db.execute(select(PemakaianAI).where(
    PemakaianAI.user_id == u.id)).scalar_one_or_none()
if p is not None:
    p.jumlah_revisi = 0
    db.commit()
    print(f'kuota user {u.id} direset → 0')

print(f'naskah : {fb.nama_simpan} ({fb.ukuran:,} byte)')
print(f'user   : id={u.id} paket={u.paket}')


class ReqTiruan:                                                          # noqa: D101
    def __init__(self, body):
        self._b = body

    async def json(self):
        return self._b


body = {
    'file_id': fb.id,
    'bab': '__seluruh__',
    'komentar': [k.isi or 'perbaiki bagian ini'],
    'setuju_bagian': True,
}

print('\n── ai_revisi() SUNGGUHAN (endpoint yg dipakai worker) ──')
t0 = time.time()
try:
    hasil = asyncio.run(A.ai_revisi(ReqTiruan(body), u, db))
    print(f'✅ SELESAI {time.time()-t0:.1f} dtk')
    print('   hasil:', str(hasil)[:220])
except Exception as e:                                                    # noqa: BLE001
    print(f'❌ GAGAL {time.time()-t0:.1f} dtk · {type(e).__name__}: {str(e)[:250]}')

print('\n══ SEMUA PANGGILAN HTTP (urut waktu) ══')
for i, c in enumerate(PANGGILAN, 1):
    print(f'  #{i} t+{c["mulai"]-t0:7.1f}s · {c["detik"]:>6.1f} dtk · '
          f'{c["status"]:<22} · {c["model"][:38]}')
    print(f'      kar={c["kar"]:,} · url={c["url"][:70]}')
    if c['awal']:
        print(f'      awal={c["awal"][:110]}')
if not PANGGILAN:
    print('  (TIDAK ADA panggilan HTTP keluar)')
