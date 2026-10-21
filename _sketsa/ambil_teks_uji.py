#!/usr/bin/env python3
"""Ambil TEKS naskah uji (host, pakai PyMuPDF) → simpan .txt untuk Jev.

Container produksi TIDAK dipakai untuk PDF (tak punya fitz & memang tak
boleh ditambah). Teks dikirim ke container sebagai .txt.
"""
from __future__ import annotations

import sys
from pathlib import Path

PETA = Path('/opt/data/services/eduai-publishing/_contoh-dokumen/uji-kedalaman')
KEL = Path('/opt/data/services/eduai-publishing/_naskah_uji_teks')
KEL.mkdir(parents=True, exist_ok=True)

nama_list = sys.argv[1:]
if not nama_list:
    nama_list = [p.name for p in sorted(PETA.glob('*.pdf'))]

import fitz  # noqa: E402

n = 0
for nama in nama_list:
    p = PETA / nama
    if not p.exists():
        print(f'  (hilang) {nama}')
        continue
    try:
        d = fitz.open(p)
        t = '\n'.join(pg.get_text() for pg in d)
        d.close()
    except Exception as e:                                    # noqa: BLE001
        print(f'  GALAT {nama}: {e}')
        continue
    kel = KEL / (Path(nama).stem + '.txt')
    kel.write_text(t, encoding='utf-8')
    n += 1
print(f'  teks tersimpan: {n} → {KEL}')
