"""BUKTI POTONGAN DOBEL: endpoint potong `jml`, lalu `_revisi_kerja` potong lagi.

HIPOTESIS (dari baca kode):
  ai_revisi()  baris 2607: for _ in range(jml): cek_dan_potong(...)   → 2
  _revisi_kerja() baris 1604: for _ in range(jml_bagian): cek_dan_potong → 2
  _revisi_kerja() baris 1985: naikkan ke token nyata (4) → +2
  TOTAL = 6  ❌  (seharusnya 4)

Uji 2 ARAH:
  A. Lewat `_revisi_kerja` SAJA (mode_tunggu dilewati) → harapan 4
  B. Lewat jalur endpoint penuh (titip latar belakang) → apakah 6?

Cara: tiru endpoint dgn memanggil `_revisi_kerja` DUA KALI lipat — tidak.
Lebih tepat: panggil fungsi endpoint `ai_revisi` langsung dgn RequestTiruan.
"""
import asyncio
import os
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, '/app')

TMP = tempfile.mkdtemp(prefix='dobel_')
shutil.copy2('/app/data/eduai.db', pathlib.Path(TMP) / 'eduai.db')
os.environ['EDUAI_DATA_DIR'] = TMP

import app.ai as A                                                    # noqa: E402
from app.models import PemakaianAI, User                              # noqa: E402
from sqlalchemy import create_engine, select                          # noqa: E402
from sqlalchemy.orm import sessionmaker                               # noqa: E402

eng = create_engine(f'sqlite:///{TMP}/eduai.db')
S = sessionmaker(bind=eng)
db = S()
u = db.get(User, 6)
bar = db.execute(select(PemakaianAI).where(
    PemakaianAI.user_id == 6)).scalar_one_or_none()
bar.jumlah_revisi = 0
db.commit()

jejak = []
_potong = A.cek_dan_potong
_kembali = A._kembalikan_kuota


def pw(db_, u_, jenis):
    r = _potong(db_, u_, jenis)
    jejak.append(('POTONG', r.get('sisa')))
    return r


def kw(db_, u_, ip):
    jejak.append(('KEMBALI', None))
    return _kembali(db_, u_, ip)


A.cek_dan_potong = pw
A._kembalikan_kuota = kw

BODY = {
    'file_id': 49,
    'komentar': ['Perbaiki kalimat pertama paragraf yang memuat '
                 '"Perkembangan pesat teknologi dan transformasi digital" — '
                 'buat lebih ringkas dan tambahkan penekanan pada tujuan '
                 'penelitian.'],
    'bab': '',
    'setuju_bagian': True,
}


async def main():
    print('═' * 68)
    print('A. Lewat ENDPOINT `ai_revisi` (mode tunggu) — jalur SUNGGUHAN')
    print('═' * 68)
    req = A._RequestTiruan(BODY)
    try:
        h = await A.ai_revisi(req, u, db, mode_tunggu=True)
        print(f'   ✅ selesai · token_revisi={h.get("token_revisi")}')
    except Exception as e:                                            # noqa: BLE001
        print(f'   ❌ {type(e).__name__}: {str(e)[:140]}')
    db.refresh(bar)
    print(f'\n   JEJAK KUOTA: {jejak}')
    print(f'   POTONG={sum(1 for x in jejak if x[0] == "POTONG")} · '
          f'KEMBALI={sum(1 for x in jejak if x[0] == "KEMBALI")}')
    print(f'   ⇒ jumlah_revisi akhir = {bar.jumlah_revisi}')
    print(f'   ⇒ HARAPAN (rumus §4.13) = 4')
    print(f'   ⇒ {"❌ DOBEL!" if bar.jumlah_revisi > 4 else "✅ BENAR"}')
    db.close()


asyncio.run(main())
