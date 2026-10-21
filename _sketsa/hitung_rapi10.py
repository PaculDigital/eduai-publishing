"""HITUNG DULU: rapi=10 dengan rumus tangga [1,2,2.5,5] × 10^n.

Cek semua kasus sebelum ubah kode (aturan: ukur dulu, baru ubah).
"""
import math

TANGGA = sorted({m * (10 ** n) for n in range(-3, 9) for m in (1, 2, 2.5, 5)})


def skala(nilai, rapi=10):
    maks = float(max(nilai) or 1)
    kandidat = [t * rapi for t in TANGGA if t * rapi >= maks]
    if not kandidat:
        return maks * 1.02, maks * 1.02 / rapi
    return kandidat[0], kandidat[0] / rapi


KASUS = [(53, 30), (20, 15), (1900, 800), (7, 7), (5, 4), (1.2, 0.8),
         (0.35, 0.2), (87000, 45000), (128, 96), (3, 2, 1), (2.7, 1.9),
         (42, 30), (100, 80), (0.72, 0.55), (250000, 120000), (15, 12)]

print(f'{"maks":>9} {"atas":>9} {"langkah":>9} {"kosong":>7}  label')
for d in KASUS:
    b, l = skala(list(d))
    kosong = (1 - max(d) / b) * 100
    lab = ' '.join(f'{l * i:g}' for i in range(11))
    tanda = '✅' if kosong <= 35 else '⚠️'
    print(f'{max(d):>9g} {b:>9g} {l:>9g} {kosong:>6.0f}% {tanda} {lab}')
