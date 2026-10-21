"""UKUR: apa isi kandidat surveyor sekarang (8.555) — sebelum disaring.

Tujuan: tahu KOMPOSISI bahan yang dikirim ke Jev, supaya penyaringan
berbasis FAKTA OBJEKTIF (bukan tebakan bentuk naskah).
"""
from __future__ import annotations

import re
import sys
from collections import Counter

sys.path.insert(0, '/app')

import peta3_jev as P                                      # noqa: E402

for fid in (115, 81, 104):
    d = P.susun(fid)
    baris, kand = d['baris'], d['kand']
    print(f'=== fid={fid}: {len(kand)} kandidat dari {len(baris)} baris '
          f'({100*len(kand)/len(baris):.1f}%) ===')

    c = Counter()
    for i, t in kand:
        s = t.strip()
        L = len(s)
        if not s:
            c['KOSONG'] += 1
        elif L <= 40:
            c['pendek<=40'] += 1
        elif L <= 80:
            c['sedang<=80'] += 1
        elif L <= 150:
            c['panjang<=150'] += 1
        else:
            c['sangat>150'] += 1
        # fakta objektif lain
        if re.match(r'^\d+(\.\d+)*[.)]?\s', s):
            c['bernomor'] += 1
        if re.match(r'^[A-Z].{0,90}$', s) and len(s) <= 95:
            c['awal-kapital<=95'] += 1
        if L and s[-1] in '.!?':
            c['diakhiri-titik'] += 1
        if L > 300:
            c['>300kar'] += 1

    for k, v in c.most_common():
        print(f'   {k:18s} {v:6d}  ({100*v/len(kand):5.1f}%)')
    print()
