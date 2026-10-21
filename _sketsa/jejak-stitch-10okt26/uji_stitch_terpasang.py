"""UJI PASANG: Pass-1 stitch di surveyor — 3 naskah.

Yang diukur: (a) kandidat turun berapa? (b) judul asli masih ada?
             (c) isi TIDAK hilang? (d) naskah normal tak berubah?
"""
from __future__ import annotations

import sys
import time

sys.path.insert(0, '/app')

import peta3_jev as P                                          # noqa: E402


def main():
    for fid in (115, 104, 81):
        t0 = time.time()
        d = P.susun(fid)
        b, k = d['baris'], d['kand']
        print(f'=== fid={fid} ===  ({time.time()-t0:.0f} dtk)')
        print(f'   baris {len(b):6d} | kandidat {len(k):6d} | buang {len(d["buang"]):5d}')
        sampah = sum(1 for x in b if len(x.strip()) <= 2)
        print(f'   sampah <=2 kar: {sampah}')
        # judul penting masih ada?
        penting = ('LATAR BELAKANG', 'TINJAUAN', 'METODE', 'HASIL', 'KESIMPULAN')
        for kata in penting:
            n = sum(1 for _i, x in k if kata in x.upper())
            print(f'      {kata:15s} {n}')
        print()


if __name__ == '__main__':
    main()
