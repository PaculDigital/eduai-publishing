"""BONGKAR: _revisi_kerja gagal → CETAK isi variabel di tiap tahap.

Karena kegagalan BERHASIL direproduksi, sekarang kita sisipkan pencatat
lewat pembungkus (wrapper) fungsi-fungsi kunci — TANPA mengubah ai.py.
"""
import asyncio
import os
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, '/app')

TMP = tempfile.mkdtemp(prefix='bongkar_')
shutil.copy2('/app/data/eduai.db', pathlib.Path(TMP) / 'eduai.db')
os.environ['EDUAI_DATA_DIR'] = TMP

import app.ai as A                                                    # noqa: E402
from app.models import User                                           # noqa: E402
from sqlalchemy import create_engine                                  # noqa: E402
from sqlalchemy.orm import sessionmaker                               # noqa: E402

#  ── BUNGKUS fungsi kunci supaya terlihat dipanggil berapa kali & hasilnya ──
_asli_potong = A.potong_cerdas
_asli_bersih = A.bersihkan_jawaban_ai
_asli_fail = A._revisi_dengan_failover
_asli_valid = A._valid

catat = []


def potong_wrap(teks, maks=None):
    r = _asli_potong(teks, maks) if maks else _asli_potong(teks)
    catat.append(('potong_cerdas', len(teks or ''), len(r),
                  [len(x) for x in r]))
    print(f'   [jejak] potong_cerdas({len(teks or ""):,}) → {len(r)} bagian '
          f'{[len(x) for x in r]}')
    return r


def bersih_wrap(konten, naskah=None):
    r = _asli_bersih(konten, naskah)
    catat.append(('bersih', len(konten or ''), len(r or '')))
    print(f'   [jejak] bersihkan({len(konten or ""):,}) → {len(r or ""):,}')
    return r


async def fail_wrap(pesan, jml, naskah_banding=None):
    print(f'   [jejak] ▸ PANGGIL AI (pesan {len(pesan):,} kar, '
          f'banding {len(naskah_banding or "") if naskah_banding else 0:,} kar)')
    r = await _asli_fail(pesan, jml, naskah_banding=naskah_banding)
    print(f'   [jejak] ◂ AI BALAS {len(r[0] or ""):,} kar · '
          f'tok in/out {r[2].get("token_in", 0):,}/{r[2].get("token_out", 0):,}')
    return r


A.potong_cerdas = potong_wrap
A.bersihkan_jawaban_ai = bersih_wrap
A._revisi_dengan_failover = fail_wrap

body = {
    'file_id': 49,
    'komentar': ['Perbaiki kalimat pertama paragraf yang memuat '
                 '"Perkembangan pesat teknologi dan transformasi digital" — '
                 'buat lebih ringkas dan tambahkan penekanan pada tujuan '
                 'penelitian.'],
    'bab': '',
    'setuju_bagian': True,
}

eng = create_engine(f'sqlite:///{TMP}/eduai.db')
db = sessionmaker(bind=eng)()
u = db.get(User, 6)


async def main():
    print('── JEJAK PEMANGGILAN ──')
    try:
        hasil = await A._revisi_kerja(A._RequestTiruan(body), u, db)
        print('\n✅ SELESAI')
        print(f'   jawaban = {len(hasil.get("jawaban") or ""):,} kar')
        print(f'   token in/out = {hasil.get("token_in")}/{hasil.get("token_out")}')
    except Exception as e:                                            # noqa: BLE001
        print(f'\n❌ GAGAL: {type(e).__name__}: {str(e)[:200]}')
    print('\n── RINGKASAN JEJAK ──')
    for c in catat:
        print('  ', c)


asyncio.run(main())
