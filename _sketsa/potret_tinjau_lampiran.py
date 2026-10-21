"""POTRET HALAMAN TINJAU + LAMPIRAN (Tahap 2.2, 24Sep26).

Memakai ALAT YANG SUDAH ADA & TERBUKTI: `potret_cdp.potret()` —
sudah menangani jebakan `captureBeyondViewport` + tutup tab.

PAKAI:
  python3 _sketsa/potret_tinjau_lampiran.py <TOKEN> [dir_keluar]
"""

import os
import sys

sys.path.insert(0, '/tmp')          # potret_cdp.py disalin ke sini
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import potret_cdp as PC                                   # noqa: E402


def main():
    token = sys.argv[1]
    keluar = sys.argv[2] if len(sys.argv) > 2 else '/tmp/tinjau_potret'
    os.makedirs(keluar, exist_ok=True)
    url = f'http://eduai-app:8000/tinjau/{token}'

    print('── 1. Lebar (seperti orang buka di laptop) ──')
    PC.potret(url, f'{keluar}/01-halaman.png', lebar=1280, tinggi=1600,
              tunggu=7)

    print('── 2. HP (kolom sempit) ──')
    PC.potret(url, f'{keluar}/02-hp.png', lebar=390, tinggi=1500, tunggu=7)

    print(f'selesai → {keluar}')


if __name__ == '__main__':
    main()
