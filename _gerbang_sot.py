#!/usr/bin/env python3
"""GERBANG SOT — pastikan DOKUMEN tidak bertabrakan dengan KODE.

Dijalankan dari DALAM container `eduai-app` (pola gerbang EduAi).
Bedanya dengan `sot.py` biasa: skrip ini MEMBACA dokumen dari /app/sot-dok/
(salinan yang disiapkan jalankan_semua_gerbang.sh) karena container tidak
punya folder proyek lengkap.

CARA PAKAI (dari jalankan_semua_gerbang.sh):
    docker cp sot.py eduai-app:/app/
    docker cp MASTER_PLAN.md FLAG_LANJUT_DISINI.md CATATAN_PROYEK.md \
        eduai-app:/app/sot-dok/
    docker exec -w /app eduai-app python3 _gerbang_sot.py
"""
from __future__ import annotations

import os
import pathlib
import sys

#  Arahkan sot.py membaca DOKUMEN dari /app/sot-dok (kurangi dari container)
_env = os.environ.get('SOT_DOK_DIR', '/app/sot-dok')
if pathlib.Path(_env).is_dir():
    os.environ['SOT_DIREKTORI_DOKUMEN'] = _env

sys.path.insert(0, '/app')

try:
    import sot  # noqa: E402  (skrip ini memakai mesin SOT yang sama)
except ImportError as e:
    print(f'TOTAL: 0 LULUS / 1 GAGAL  — gagal import sot.py: {e}')
    raise SystemExit(1)


def main() -> int:
    d = sot.kumpulkan()
    masalah = sot.periksa(d)
    if masalah == 0:
        print(f'TOTAL: {len(sot.PERAN_DOKUMEN)} LULUS / 0 GAGAL '
              f'(SOT selaras: image={d["image"]}, {d["tabel"]} tabel, '
              f'{d["gerbang"]} gerbang)')
        return 0
    print(f'TOTAL: 0 LULUS / {masalah} GAGAL (dokumen bertabrakan dengan kode)')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
