"""UJI NYATA: periksa_mutu terhadap 3 NASKAH SUNGGUHAN (dari DB user).

Sekaligus mengecek: apakah hasilnya SAMA dengan pengukuran awal
Asih=1 · PDF=4.989 · Disertasi=1 (huruf tunggal).
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR   # noqa: E402
from app.models import FileBerkas                                 # noqa: E402
from app.periksa_mutu import periksa                              # noqa: E402

for fid, nama in ((81, 'Asih (SEHAT)'), (115, 'Wulandari-PDF (RUSAK)'),
                  (104, 'Disertasi (baris pendek)')):
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        if not fb:
            print(f'fid={fid}: tidak ada')
            continue
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        teks = _teks_dari_berkas(p, fb.nama or '') or ''
    finally:
        db.close()
    m = periksa(teks)
    print(f'── fid={fid} — {nama} ──')
    print(f'   tingkat       : {m["tingkat"]}')
    print(f'   huruf tunggal : {m["huruf_tunggal"]}')
    print(f'   baris <=2 kar : {m["rasio_pendek"]*100:.0f}%')
    print(f'   median        : {m["median"]:.0f} kar')
    print(f'   saran         : {m["saran"]}')
    print(f'   pesan         : {m["pesan"][:160]}')
    print()
