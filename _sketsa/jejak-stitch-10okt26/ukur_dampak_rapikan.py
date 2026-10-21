"""UKUR DAMPAK _rapikan_baris pada KANDIDAT SURVEYOR (3 naskah).

Pertanyaan: berapa kandidat SETELAH baris per-huruf disambung?
Harapan: kandidat turun drastis, DAN judul asli tetap ada.
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

import peta3_jev as P                                        # noqa: E402
import _rapikan_baris as RB                                  # noqa: E402


def hitung(baris_teks: list[str], nama: str):
    d = P.susun.__wrapped__(baris_teks) if hasattr(P.susun, '__wrapped__') else None
    return d


def main():
    hasil = {}
    for fid in (81, 115, 104):
        d = P.susun(fid)
        b0 = d['baris']
        # SEBELUM
        k0 = len(d['kand'])
        p0 = sum(1 for x in b0 if len(x.strip()) <= 2)
        # SESUDAH rapikan
        h = RB.rapikan('\n'.join(b0)).split('\n')
        p1 = sum(1 for x in h if len(x.strip()) <= 2)
        hasil[fid] = {'b0': len(b0), 'k0': k0, 'p0': p0, 'b1': len(h), 'p1': p1}
        print(f'=== fid={fid} ===')
        print(f'   SEPARUH: {len(b0):6d} baris | {k0:6d} kandidat | {p0:5d} sampah<=2 ({100*p0/len(b0):.0f}%)')
        print(f'   RAPIKAN: {len(h):6d} baris | {p1:5d} sampah<=2')
        print()
    return hasil


if __name__ == '__main__':
    sys.exit(0 if main() else 0)
