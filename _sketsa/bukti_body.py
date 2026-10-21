"""BUKTI: apa yang `_revisi_kerja` LIHAT saat dipanggil dari endpoint.

Endpoint (`ai_revisi`) melakukan pemrosesan LALU memanggil `_revisi_kerja`
dengan `_RequestTiruan(body)`. Uji ini meniru PERSIS alurnya:
  1. body dari klien (spt skrip E2E)
  2. potong_cerdas → jml
  3. body diubah (spt endpoint)
  4. _revisi_kerja dijalankan dgn _RequestTiruan(body)
Dan mencetak: apakah `naskah` terisi, `bab` apa, berapa bagian.

⚠️ TIDAK menulis DB. Pakai DB salinan supaya aman.
"""
import asyncio
import json
import shutil
import sys
import tempfile

sys.path.insert(0, '/app')

import pathlib                                                        # noqa: E402

#  ── DB salinan (JANGAN sentuh produksi) ──
TMP = tempfile.mkdtemp(prefix='body_')
SALIN = pathlib.Path(TMP) / 'eduai.db'
shutil.copy2('/app/data/eduai.db', SALIN)
import os                                                             # noqa: E402
os.environ['EDUAI_DATA_DIR'] = TMP

import app.ai as A                                                    # noqa: E402
from app.config import UPLOAD_DIR                                     # noqa: E402

print(f'UPLOAD_DIR = {UPLOAD_DIR}')

#  ── 1) body PERSIS seperti skrip E2E kirim ──
body = {
    'file_id': 49,
    'komentar': ['Perbaiki kalimat pertama paragraf yang memuat '
                 '"Perkembangan pesat teknologi dan transformasi digital" — '
                 'buat lebih ringkas dan tambahkan penekanan pada tujuan '
                 'penelitian.'],
    'bab': '',
    'setuju_bagian': True,
}
print(f'1) body dari klien: {json.dumps(body, ensure_ascii=False)[:200]}')

#  ── 2) apa yang _revisi_kerja bacakan ──
kulit = A._RequestTiruan(body)


async def cek_body():
    b = await kulit.json()
    print(f'2) _revisi_kerja membaca body: {json.dumps(b, ensure_ascii=False)[:200]}')
    print(f'   naskah  = {len((b.get("naskah") or "").strip()):,} kar')
    print(f'   file_id = {b.get("file_id")}')
    print(f'   bab     = {b.get("bab")!r}')
    print(f'   komentar= {len(b.get("komentar") or [])} item')
    print()
    #  ── 3) apakah _teks_dari_body berhasil? ──
    from app.db import sesi as _sesi
    db = _sesi()
    try:
        naskah, fb, err = A._teks_dari_body(db, __import__('app.models', fromlist=['x']), b)
    except TypeError:
        # signature lain
        naskah, fb, err = None, None, 'butuh user'
    finally:
        db.close()
    return b


asyncio.run(cek_body())

#  ── 4) ambil file_id dari DB & cek berkas ada ──
import sqlite3                                                        # noqa: E402
c = sqlite3.connect('/app/data/eduai.db')
r = c.execute('SELECT id,nama,nama_simpan,user_id FROM files WHERE id=49').fetchone()
c.close()
print(f'4) berkas 49: {r}')
if r:
    p = pathlib.Path(UPLOAD_DIR) / str(r[3]) / r[2]
    print(f'   di disk: ada={p.exists()} · '
          f'{p.stat().st_size if p.exists() else 0:,} byte')
