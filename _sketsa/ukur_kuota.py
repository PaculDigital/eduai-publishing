"""UKUR: kenapa kuota terpakai 6 padahal token_revisi_nyata = 4?

Hipotesis: gerbang memotong `jml_bagian` = 6? Atau penyesuaian (baris 1994)
tidak jalan karena `info_potong` cuma berisi 2?

Uji ini memanggil `_revisi_kerja` langsung + mencetak `info_potong` & kuota
sebelum/sesudah.
"""
import asyncio
import os
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, '/app')

TMP = tempfile.mkdtemp(prefix='kuota_')
shutil.copy2('/app/data/eduai.db', pathlib.Path(TMP) / 'eduai.db')
os.environ['EDUAI_DATA_DIR'] = TMP

import app.ai as A                                                    # noqa: E402
from app.models import User                                           # noqa: E402
from app.kuota import ringkasan_kuota                                 # noqa: E402
from sqlalchemy import create_engine                                  # noqa: E402
from sqlalchemy.orm import sessionmaker                               # noqa: E402

eng = create_engine(f'sqlite:///{TMP}/eduai.db')
db = sessionmaker(bind=eng)()
u = db.get(User, 6)

#  ── reset kuota 0 dulu supaya terukur bersih ──
from app.models import PemakaianAI                                    # noqa: E402
from sqlalchemy import select                                         # noqa: E402
bar = db.execute(select(PemakaianAI).where(
    PemakaianAI.user_id == 6)).scalar_one_or_none()
print(f'SEBELUM: jumlah_revisi={bar.jumlah_revisi}')
bar.jumlah_revisi = 0
db.commit()
print('reset → 0\n')

#  ── bungkus cek_dan_potong & _kembalikan_kuota untuk HITUNG ──
_asli_potong = A.cek_dan_potong
_asli_kembali = A._kembalikan_kuota
jejak = {'potong': 0, 'kembali': 0}


def potong_wrap(db_, u_, jenis):
    r = _asli_potong(db_, u_, jenis)
    jejak['potong'] += 1
    print(f"   [KUOTA] potong #{jejak['potong']} → {r.get('sisa')}")
    return r


def kembali_wrap(db_, u_, ip):
    jejak['kembali'] += 1
    print(f"   [KUOTA] KEMBALI #{jejak['kembali']}")
    return _asli_kembali(db_, u_, ip)


A.cek_dan_potong = potong_wrap
A._kembalikan_kuota = kembali_wrap


body = {
    'file_id': 49,
    'komentar': ['Perbaiki kalimat pertama paragraf yang memuat '
                 '"Perkembangan pesat teknologi dan transformasi digital" — '
                 'buat lebih ringkas dan tambahkan penekanan pada tujuan '
                 'penelitian.'],
    'bab': '',
    'setuju_bagian': True,
}


async def main():
    try:
        h = await A._revisi_kerja(A._RequestTiruan(body), u, db)
        print(f"\n✅ SELESAI · token_revisi={h.get('token_revisi')} "
              f"bagian={h.get('bagian')}")
        print(f"   token in/out = {h.get('token_in')}/{h.get('token_out')}")
    except Exception as e:                                            # noqa: BLE001
        print(f'\n❌ {type(e).__name__}: {str(e)[:160]}')
    db.refresh(bar)
    print(f"\nSESUDAH: jumlah_revisi={bar.jumlah_revisi} (terpakai)")
    print(f"JEJAK: potong={jejak['potong']} · kembali={jejak['kembali']}")
    print(f"⇒ terpakai {bar.jumlah_revisi} = potong {jejak['potong']} "
          f"- kembali {jejak['kembali']}")
    db.close()


asyncio.run(main())
