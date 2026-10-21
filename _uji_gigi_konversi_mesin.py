#!/usr/bin/env python3
"""UJI GIGI TAHAP 2 — buktikan gerbang mesin BISA GAGAL kalau kode dirusak.

Menyuntik 4 kerusakan nyata ke `app/konversi.py` di container, jalankan ulang
gerbang, lalu PULIHKAN. Gerbang yang selalu lulus = palsu.

Suntikan:
  (1) periksa_berkas_aman() selalu True → makro LOLOS (bahaya keamanan)
  (2) cari_identitas() selalu kosong    → pagar nama jadi palsu
  (3) ELEMEN_11 dikosongkan            → pemeriksa buta
  (4) muat_prompt() kembalikan ''      → prompt hilang tak terdeteksi

Jalankan dari HOST:
    python3 _uji_gigi_konversi_mesin.py
"""
from __future__ import annotations

import subprocess
import sys

KONTAINER = 'eduai-app'
KODE = '/app/app/konversi.py'

SUNTIKAN = [
    ('(1) pagar makro selalu LOLOS',
     "    ekst = Path(nama or '').suffix.lower()",
     "    return True, ''\n    ekst = Path(nama or '').suffix.lower()"),
    ('(2) cari_identitas selalu kosong',
     "    hasil = {'nama': '', 'email': ''}\n    teks = naskah or ''",
     "    return {'nama': '', 'email': ''}\n    teks = naskah or ''"),
    ('(3) ELEMEN_11 dikosongkan',
     "    ('hook',              'Hook',                   'Pendahuluan ¶1'),",
     "    ('hook',              'Hook',                   'Pendahuluan ¶1'),\n] if False else [\n    ('hook',              'Hook',\n     'Pendahuluan ¶1'),"),
    ('(4) prompt hilang (muat_prompt -> "")',
     "    try:\n        return PROMPT_ARTIKEL.read_text(encoding='utf-8')",
     "    try:\n        return ''"),
]


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True)


def baca() -> str:
    return sh('docker', 'exec', KONTAINER, 'cat', KODE).stdout


def tulis(isi: str) -> None:
    subprocess.run(['docker', 'exec', '-i', KONTAINER, 'sh', '-c', f'cat > {KODE}'],
                   input=isi, text=True, capture_output=True, check=True)


def main() -> int:
    asli = baca()
    if not asli.strip():
        print('❌ gagal baca konversi.py'); return 2
    tulis(asli)

    lewat = 0
    for nama, cari, ganti in SUNTIKAN:
        if cari not in asli:
            print(f'⚠️  {nama} — pola TIDAK KETEMU (suntikan tak terpasang)')
            lewat += 1
            continue
        tulis(asli.replace(cari, ganti, 1))
        r = sh('docker', 'exec', '-w', '/app', KONTAINER, 'python3',
               '_gerbang_konversi_mesin.py')
        tertangkap = r.returncode != 0
        tanda = '✅ TERTANGKAP' if tertangkap else '❌ LOLOS (gerbang PALSU!)'
        if not tertangkap:
            lewat += 1
        n = r.stdout.count('❌')
        print(f'{tanda}  {nama}  (exit={r.returncode}, asersi gagal={n})')
        tulis(asli)

    tulis(asli)
    r = sh('docker', 'exec', '-w', '/app', KONTAINER, 'python3',
           '_gerbang_konversi_mesin.py')
    print(f'\nPulih: gerbang kembali exit={r.returncode} '
          f'({r.stdout.count("✅")} lulus)')
    if r.returncode != 0:
        print('❌ GAGAL memulihkan konversi.py!'); return 2

    print(f'\n══ UJI GIGI: {len(SUNTIKAN)-lewat}/{len(SUNTIKAN)} '
          f'kerusakan TERTANGKAP ══')
    return 1 if lewat else 0


if __name__ == '__main__':
    sys.exit(main())
