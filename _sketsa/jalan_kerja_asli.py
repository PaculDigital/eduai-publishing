"""JALANKAN `_revisi_kerja` SUNGGUHAN — DB SALINAN, berkas ASLI.

INI UJI PENENTU: bukan tiruan, bukan impor sebagian. Fungsi asli dipanggil
dengan `_RequestTiruan` seperti jalur latar belakang, lalu kita cetak:
  - naskah terbaca berapa kar
  - berapa bagian
  - token_in (bukti AI benar-benar dipanggil)
  - jawaban

⚠️ DB = SALINAN (/tmp). UPLOAD_DIR = ASLI (berkas naskah).
"""
import asyncio
import os
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, '/app')

TMP = tempfile.mkdtemp(prefix='karja_')
shutil.copy2('/app/data/eduai.db', pathlib.Path(TMP) / 'eduai.db')
os.environ['EDUAI_DATA_DIR'] = TMP
#  ⚠️ UPLOAD_DIR JANGAN di-override → berkas naskah asli harus terbaca.

import app.ai as A                                                    # noqa: E402
from app.config import UPLOAD_DIR                                     # noqa: E402
from app.models import User                                           # noqa: E402

print(f'DATA_DIR   = {TMP}')
print(f'UPLOAD_DIR = {UPLOAD_DIR}')

body = {
    'file_id': 49,
    'komentar': ['Perbaiki kalimat pertama paragraf yang memuat '
                 '"Perkembangan pesat teknologi dan transformasi digital" — '
                 'buat lebih ringkas dan tambahkan penekanan pada tujuan '
                 'penelitian.'],
    'bab': '',
    'setuju_bagian': True,
}

from sqlalchemy import create_engine                                  # noqa: E402
from sqlalchemy.orm import sessionmaker                               # noqa: E402
eng = create_engine(f'sqlite:///{TMP}/eduai.db')
S = sessionmaker(bind=eng)
db = S()
u = db.get(User, 6)
print(f'user 6 = {u.email if u else None} · paket={getattr(u, "paket", None)}')


async def main():
    req = A._RequestTiruan(body)
    print('\n── PANGGIL _revisi_kerja SUNGGUHAN ──')
    try:
        hasil = await A._revisi_kerja(req, u, db)
        print('✅ SELESAI')
        for k in ('jawaban', 'model', 'token_in', 'token_out',
                  'token_revisi', 'bagian'):
            v = hasil.get(k)
            if k == 'jawaban' and isinstance(v, str):
                v = f'{len(v):,} kar · {v[:120]!r}'
            print(f'   {k} = {v}')
    except Exception as e:                                            # noqa: BLE001
        print(f'❌ GAGAL: {type(e).__name__}: {str(e)[:400]}')
    finally:
        db.close()


asyncio.run(main())
