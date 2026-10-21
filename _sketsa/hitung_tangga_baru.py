"""CARI ATURAN FINAL YANG SELESAI — bukan menambal.

MASALAH TERSISA (rapi=10, tangga 1/2/2.5/5):
   maks 53 → 100 (47% kosong) · 128 → 200 (36%) · 3 → 5 (40%) · 2.7 → 5 (46%)

POLA: angka "di tengah" antara dua anak tangga (53 antara 50 & 60;
      128 antara 125 & 150; 3 antara 2.5 & 4; 2.7 antara 2.5 & 5).

IDE PENUTUP (paling sederhana, tanpa rumus baru):
   Tambahkan LANGKAH ANTARA ke tangga: 3, 4, 6, 7.5, 8  (dan puluhan/ratusannya)
   → 53  : langkah 5.4? tidak ada → 6   → batas 60  ✅ (12%)
   → 128 : langkah 14? tidak ada → 15   → batas 150 ✅ (15%)
   → 3   : langkah 0.3 → batas 3       ✅ (0%)
   → 2.7 : langkah 0.3 → batas 3       ✅ (10%)
   → 1.2 : langkah 0.15? → 0.15×10=1.5 ✅ (20%)

UJI DULU SEBELUM UBAH KODE.
"""


def bangun_tangga():
    """Tangga 'enak dibaca' — tambah 3, 4, 6, 7.5, 8 (dan kelipatan 10^n).

    Angka-angka ini BUKAN karangan: ini yang dipakai skala penggaris,
    termometer, dan sumbu grafik Excel/Tableau (0.3, 1.5, 4, 6, 8, 15, 40).
    """
    inti = (1, 1.5, 2, 2.5, 3, 4, 5, 6, 7.5, 8)
    out = set()
    for n in range(-3, 9):
        for m in inti:
            out.add(m * (10 ** n))
    return sorted(out)


TANGGA = bangun_tangga()


def skala(nilai, rapi=10):
    maks = float(max(nilai) or 1)
    kandidat = [t * rapi for t in TANGGA if t * rapi >= maks]
    if not kandidat:
        return maks * 1.02, maks * 1.02 / rapi
    return kandidat[0], kandidat[0] / rapi


KASUS = [(53, 30), (20, 15), (1900, 800), (7, 7), (5, 4), (1.2, 0.8),
         (0.35, 0.2), (87000, 45000), (128, 96), (3, 2, 1), (2.7, 1.9),
         (42, 30), (100, 80), (0.72, 0.55), (250000, 120000), (15, 12),
         (63, 40), (250, 180), (0.98, 0.6), (9, 6), (44, 33), (3600, 2400),
         (0.125, 0.09), (12.5, 9), (777, 500)]

print(f'{"maks":>9} {"atas":>9} {"langkah":>9} {"kosong":>7}  tanda')
gagal = 0
for d in KASUS:
    b, l = skala(list(d))
    kosong = (1 - max(d) / b) * 100
    tanda = '✅' if kosong <= 25 else '⚠️'
    if kosong > 25:
        gagal += 1
    print(f'{max(d):>9g} {b:>9g} {l:>9g} {kosong:>6.0f}% {tanda}')

print(f'\n⇒ {len(KASUS) - gagal}/{len(KASUS)} LULUS (kanvas terpakai ≤ 25% kosong)')
print(f'   gagal: {gagal}')
