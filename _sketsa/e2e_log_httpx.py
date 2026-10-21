"""E2E NYATA dgn LOG httpx DIBUKA — cari BOTTLE NECK jalur latar belakang.

PERTANYAAN BOS 25Sep26: kenapa E2E gagal 420-460 dtk dengan token_in=0,
padahal uji langsung 9router 15-47 dtk SELALU sukses?

CARA:
  1. Pasang PENYADAP pada httpx.AsyncClient.post → catat tiap panggilan:
     URL, status, waktu, ukuran body, awal balasan.
  2. Jalankan `_revisi_kerja` SUNGGUHAN untuk naskah Bos (2 bagian).
  3. Cetak urutan waktu tiap panggilan → ketemu mana yang menggantung.

⚠️ TIDAK menyentuh AI produksi lewat HTTP (langsung ke fungsi, sama seperti
   uji Wulan sebelumnya yang selalu sukses). Kuota dikembalikan sendiri.
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
                        BerkasPembimbingan, SessionLocal, User)

CATATAN_ID = 106
CATATAN: list[dict] = []
POST_ASLI = httpx.AsyncClient.post


async def post_sadap(self, url, *a, **kw):
    """Catat tiap POST yang keluar, lalu teruskan ke aslinya."""
    isi = kw.get('json') or {}
    model = isi.get('model', '?')
    n_kar = len(str(isi.get('messages') or ''))
    t0 = time.time()
    CATATAN.append({'url': str(url), 'model': model, 'kar': n_kar,
                    'mulai': t0, 'status': 'jalan'})
    baris = CATATAN[-1]
    try:
        r = await POST_ASLI(self, url, *a, **kw)
        baris.update(status=f'HTTP {r.status_code}',
                     detik=round(time.time() - t0, 1),
                     awal=(r.text or '')[:150].replace('\n', ' '))
        return r
    except Exception as e:                                                 # noqa: BLE001
        baris.update(status=f'EXC {type(e).__name__}',
                     detik=round(time.time() - t0, 1),
                     awal=str(e)[:150])
        raise


httpx.AsyncClient.post = post_sadap

print('═' * 78)
print('  E2E NYATA — LOG httpx DIBUKA')
print('═' * 78)

db = SessionLocal()
k = db.execute(select(CatatanPembimbing).where(
    CatatanPembimbing.id == CATATAN_ID)).scalar_one_or_none()
pb = db.execute(select(BerkasPembimbingan).where(
    BerkasPembimbingan.id == k.berkas_id)).scalar_one_or_none()
fb = db.execute(select(FileBerkas).where(
    FileBerkas.id == pb.file_id)).scalar_one_or_none()
u = db.execute(select(User).where(User.id == fb.user_id)).scalar_one()

p = Path('/app/uploads') / str(fb.user_id) / fb.nama_simpan
print(f'naskah : {fb.nama_simpan} ({fb.ukuran:,} byte) · ada={p.exists()}')


class ReqTiruan:                                                           # noqa: D101
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

print('\n── jalankan _revisi_kerja SUNGGUHAN ──')
t0 = time.time()
try:
    hasil = asyncio.run(A._revisi_kerja(ReqTiruan(body), u, db))
    print(f'SELESAI {time.time()-t0:.1f} dtk · {str(hasil)[:200]}')
except Exception as e:                                                     # noqa: BLE001
    print(f'GAGAL {time.time()-t0:.1f} dtk · {type(e).__name__}: {str(e)[:250]}')

print('\n══ CATATAN PANGGILAN (urut waktu) ══')
for i, c in enumerate(CATATAN, 1):
    print(f'  #{i} t+{c["mulai"]-t0:6.1f}s · {c["detik"] if "detik" in c else "?":>6} dtk'
          f' · {c["status"]:<28} · model={c["model"][:40]}')
    print(f'       url  = {c["url"][:100]}')
    print(f'       kar  = {c["kar"]:,} · awal={c.get("awal","")[:110]}')

if not CATATAN:
    print('  (TIDAK ADA panggilan HTTP keluar sama sekali — '
          'berarti berhenti SEBELUM panggil AI)')
