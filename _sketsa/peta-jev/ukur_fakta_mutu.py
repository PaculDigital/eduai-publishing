"""UKUR FAKTA MUTU NASKAH — bahan sketsa pintu periksa (10 Okt 2026).

Hitung 3 FAKTA OBJEKTIF dari teks naskah (bukan menebak bentuk):
  ① persen baris <= 2 karakter (tanda pecah per-huruf)
  ② persen baris 3-25 karakter
  ③ median panjang baris berisi
  ④ apakah ada baris berisi HANYA 1 huruf (a-z tunggal)
"""
from __future__ import annotations

import statistics
import sys

sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR   # noqa: E402
from app.models import FileBerkas                                 # noqa: E402
import app.state as S                                             # noqa: E402


def fakta(bersih: str) -> dict:
    baris = [x.strip() for x in bersih.split('\n')]
    isi = [x for x in baris if x]
    if not isi:
        return {}
    n = len(isi)
    p2 = sum(1 for x in isi if len(x) <= 2)
    p25 = sum(1 for x in isi if 3 <= len(x) <= 25)
    satu = sum(1 for x in isi if len(x) == 1 and x.isalpha())
    return {
        'baris': n,
        'le2': p2, 'le2_pct': 100 * p2 / n,
        '3_25': p25, '3_25_pct': 100 * p25 / n,
        'median': statistics.median(len(x) for x in isi),
        'huruf_tunggal': satu,
    }


for fid, nama in ((81, 'Asih (normal)'), (115, 'Wulandari-PDF'),
                  (104, 'Disertasi')):
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        if not fb:
            print(f'fid={fid}: TIDAK ADA')
            continue
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        bersih = S.buang_daftar_isi(_teks_dari_berkas(p, fb.nama or '') or '')
    finally:
        db.close()
    f = fakta(bersih)
    print(f'── fid={fid} ({nama}) ──')
    print(f'   baris berisi      : {f["baris"]}')
    print(f'   baris <=2 kar     : {f["le2"]} ({f["le2_pct"]:.0f}%)')
    print(f'   baris 3-25 kar    : {f["3_25"]} ({f["3_25_pct"]:.0f}%)')
    print(f'   huruf tunggal     : {f["huruf_tunggal"]}')
    print(f'   median panjang    : {f["median"]:.0f} kar')
    print()
