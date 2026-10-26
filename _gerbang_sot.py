#!/usr/bin/env python3
"""GERBANG SOT — pastikan DOKUMEN tidak bertabrakan dengan KODE.

Dijalankan dari DALAM container `eduai-app` (pola gerbang EduAi).
Bedanya dengan `sot.py` biasa: skrip ini MEMBACA dokumen dari /app/sot-dok/
(salinan yang disiapkan jalankan_semua_gerbang.sh) karena container tidak
punya folder proyek lengkap.

CARA PAKAI (dari jalankan_semua_gerbang.sh):
    docker cp sot.py eduai-app:/app/
    docker cp sot.py eduai-app:/app/sot-dok/sot.py
    docker cp SOT.md eduai-app:/app/sot-dok/
    docker cp docs/sot/*.md eduai-app:/app/sot-dok/docs/sot/
    docker cp _sketsa/jalankan_semua_gerbang.sh \
        eduai-app:/app/sot-dok/_sketsa/
    docker cp *.md eduai-app:/app/sot-dok/   # lampiran root
    docker exec -w /app eduai-app python3 _gerbang_sot.py

BERGIGI (26 Okt 2026, temuan agen Boss A): gerbang ini TIDAK BOLEH lulus
hanya karena sot.periksa() = 0. Ia juga memeriksa keberadaan SETIAP berkas
di sot.PERAN_DOKUMEN di dalam /app/sot-dok/ (kecuali sot.py yang juga sah
di /app/sot.py). Berkas PERAN yang hilang = GAGAL, bukan dilewati diam-diam.
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
    #  BERGIGI (lanjutan, temuan agen Boss ronde 2, butir 2): sejak
    #  sot.periksa() sendiri sudah menghitung berkas PERAN yang hilang
    #  (periksa_berkas_peran), gerbang ini TIDAK BOLEH menghitungnya
    #  2 kali. Satu-satunya yang masih ditambahkan di sini adalah
    #  'sot.py' — pemeriksa itu sendiri, yang sengaja dikecualikan
    #  dari periksa_berkas_peran karena adanya dibuktikan oleh
    #  berjalannya skrip ini. Di container, sot.py sah di /app/sot.py
    #  (salinan utama gerbang) maupun di sot-dok/sot.py (salinan gerbang).
    #  Daftar hilang tetap dicetak sebagai rincian, supaya jelas berkas
    #  mana yang hilang, bukan hanya angka.
    dok_dir = pathlib.Path(getattr(sot, 'DOK_DIR', _env))
    hilang = []
    for nama in sot.PERAN_DOKUMEN:
        p = dok_dir / nama
        if nama == 'sot.py' and not p.exists():
            if pathlib.Path('/app/sot.py').exists():
                continue
        if not p.exists():
            hilang.append(nama)
    sot_py_hilang = 1 if 'sot.py' in hilang else 0
    total_gagal = masalah + sot_py_hilang
    if total_gagal == 0:
        print(f'TOTAL: {len(sot.PERAN_DOKUMEN)} LULUS / 0 GAGAL '
              f'(SOT selaras: image={d["image"]}, {d["tabel"]} tabel, '
              f'{d["gerbang"]} gerbang)')
        return 0
    for nama in hilang:
        print(f'  ❌ BERKAS PERAN HILANG di sot-dok: {nama}')
    print(f'TOTAL: 0 LULUS / {total_gagal} GAGAL '
          f'(periksa={masalah}, sot.py hilang={sot_py_hilang})')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
