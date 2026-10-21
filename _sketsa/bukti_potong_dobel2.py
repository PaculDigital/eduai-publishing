"""BUKTI POTONGAN DOBEL — jalur SUNGGUHAN, tanpa HTTP palsu.

CARA: panggil `_revisi_kerja` DUA cara:
  A. LANGSUNG (seperti skrip uji Wulan)      → potong 2 + naik ke 4 = 4 ✅
  B. Lewat `ai_revisi()` dgn RequestTiruan   → potong 2 (endpoint)
                                                + potong 2 (_revisi_kerja)
                                                + naik ke 4 → 6 ❌

Untuk B, RequestTiruan harus punya `.json()` async.
"""
import asyncio
import os
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, '/app')

TMP = tempfile.mkdtemp(prefix='dobel2_')
shutil.copy2('/app/data/eduai.db', pathlib.Path(TMP) / 'eduai.db')
os.environ['EDUAI_DATA_DIR'] = TMP

import app.ai as A                                                    # noqa: E402
from app.models import PemakaianAI, User                              # noqa: E402
from sqlalchemy import create_engine, select                          # noqa: E402
from sqlalchemy.orm import sessionmaker                               # noqa: E402

BODY = {
    'file_id': 49,
    'komentar': ['Perbaiki kalimat pertama paragraf yang memuat '
                 '"Perkembangan pesat teknologi dan transformasi digital" — '
                 'buat lebih ringkas dan tambahkan penekanan pada tujuan '
                 'penelitian.'],
    'bab': '',
    'setuju_bagian': True,
}


class ReqTiruan:
    """Punya `.json()` async — supaya `await request.json()` di endpoint jalan."""

    def __init__(self, d):
        self._d = d

    async def json(self):
        return self._d

    @property
    def headers(self):
        return {}

    def __getattr__(self, n):
        return None


def siapkan(db, S):
    bar = db.execute(select(PemakaianAI).where(
        PemakaianAI.user_id == 6)).scalar_one_or_none()
    bar.jumlah_revisi = 0
    db.commit()
    return bar


def pasang_jejak():
    jejak = []
    _p, _k = A.cek_dan_potong, A._kembalikan_kuota

    def pw(db_, u_, j):
        r = _p(db_, u_, j)
        jejak.append('POTONG')
        return r

    def kw(db_, u_, ip):
        jejak.append('KEMBALI')
        return _k(db_, u_, ip)

    A.cek_dan_potong, A._kembalikan_kuota = pw, kw
    return jejak


async def main():
    eng = create_engine(f'sqlite:///{TMP}/eduai.db')
    S = sessionmaker(bind=eng)

    #  ══ A. LANGSUNG ke `_revisi_kerja` ══
    db1, u1 = S(), None
    u1 = db1.get(User, 6)
    bar1 = siapkan(db1, S)
    j1 = pasang_jejak()
    print('═' * 66)
    print('A. `_revisi_kerja` LANGSUNG (yang Wulan uji sebelumnya)')
    print('═' * 66)
    try:
        h = await A._revisi_kerja(A._RequestTiruan(BODY), u1, db1)
        print(f'   ✅ token_revisi={h.get("token_revisi")}')
    except Exception as e:                                            # noqa: BLE001
        print(f'   ❌ {type(e).__name__}: {str(e)[:120]}')
    db1.refresh(bar1)
    print(f'   potong={j1.count("POTONG")} · kembali={j1.count("KEMBALI")}')
    print(f'   ⇒ TERPAKAI = {bar1.jumlah_revisi}  (harapan 4)')
    db1.close()

    #  ══ B. LEWAT `ai_revisi` (endpoint, jalur nyata) ══
    db2 = S()
    u2 = db2.get(User, 6)
    bar2 = siapkan(db2, S)
    j2 = pasang_jejak()
    print('\n' + '═' * 66)
    print('B. LEWAT `ai_revisi()` — jalur SUNGGUHAN halaman')
    print('═' * 66)
    try:
        hasil = await A.ai_revisi(ReqTiruan(BODY), u2, db2)
        print(f'   ✅ endpoint balas: {str(hasil)[:110]}')
    except Exception as e:                                            # noqa: BLE001
        print(f'   ❌ {type(e).__name__}: {str(e)[:160]}')
    db2.refresh(bar2)
    print(f'   potong={j2.count("POTONG")} · kembali={j2.count("KEMBALI")}')
    print(f'   ⇒ TERPAKAI = {bar2.jumlah_revisi}  (harapan 4)')
    if bar2.jumlah_revisi > 4:
        print('   ⇒ ❌ POTONGAN DOBEL TERBUKTI')
    db2.close()


asyncio.run(main())
