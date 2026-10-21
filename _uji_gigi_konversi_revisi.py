#!/usr/bin/env python3
"""UJI GIGI TAHAP 3 & 4 — buktikan gerbang BISA GAGAL kalau kode dirusak.

Suntikan:
  (1) terapkan_revisi() menimpa SEMUA kunci (bukan hanya yang dikirim AI)
  (2) hitung_biaya_revisi() selalu 0 token (gratis = kebocoran uang)
  (3) gagalkan() tidak mengembalikan jatah (user dirugikan)

Jalankan dari HOST:  python3 _uji_gigi_konversi_revisi.py
"""
from __future__ import annotations

import subprocess
import sys

KONTAINER = 'eduai-app'
KODE = '/app/app/konversi.py'

SUNTIKAN = [
    ('(1) terapkan_revisi timpa SEMUA kunci',
     "    for k, v in j.items():\n        if k == 'elemen' and isinstance(v, dict):",
     "    barang.update(j)\n    for k, v in ({}).items():\n        if k == 'elemen' and isinstance(v, dict):"),
    ('(2) biaya revisi selalu 0 token',
     "    return {'jumlah': jumlah, 'token': jumlah * TOKEN_PER_REVISI,",
     "    return {'jumlah': jumlah, 'token': 0,"),
    ('(3) gagalkan tidak kembalikan jatah',
     "    ok = kuota.kembalikan_konversi(db, int(getattr(u, 'id', 0)), int(fid),\n                                   galat=galat)",
     "    ok = False"),
]


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True)


def baca():
    return sh('docker', 'exec', KONTAINER, 'cat', KODE).stdout


def tulis(isi):
    subprocess.run(['docker', 'exec', '-i', KONTAINER, 'sh', '-c', f'cat > {KODE}'],
                   input=isi, text=True, capture_output=True, check=True)


def main() -> int:
    asli = baca()
    if not asli.strip():
        print('❌ gagal baca'); return 2
    tulis(asli)
    lewat = 0
    for nama, cari, ganti in SUNTIKAN:
        if cari not in asli:
            print(f'⚠️  {nama} — pola TIDAK KETEMU'); lewat += 1; continue
        tulis(asli.replace(cari, ganti, 1))
        r = sh('docker', 'exec', '-w', '/app', KONTAINER, 'python3',
               '_gerbang_konversi_revisi.py')
        tertangkap = r.returncode != 0
        if not tertangkap:
            lewat += 1
        tanda = '✅ TERTANGKAP' if tertangkap else '❌ LOLOS (gerbang PALSU!)'
        print(f'{tanda}  {nama}  (exit={r.returncode}, gagal={r.stdout.count("❌")})')
        tulis(asli)
    tulis(asli)
    r = sh('docker', 'exec', '-w', '/app', KONTAINER, 'python3',
           '_gerbang_konversi_revisi.py')
    print(f'\nPulih: exit={r.returncode} ({r.stdout.count("✅")} lulus)')
    if r.returncode != 0:
        print('❌ GAGAL pulihkan!'); return 2
    print(f'\n══ UJI GIGI: {len(SUNTIKAN)-lewat}/{len(SUNTIKAN)} TERTANGKAP ══')
    return 1 if lewat else 0


if __name__ == '__main__':
    sys.exit(main())
