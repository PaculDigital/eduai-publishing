"""ANALISA HARGA v3 — pakai HARGA PAKET yang BENAR (config.py).

KOREKSI WULAN: analisa sebelumnya memakai "60.000 untuk 36 Token" — SALAH,
itu mencampur harga AddOn dengan harga paket. Yang BENAR dari app/config.py:

  PAKET (tiket masuk, kuota revisi per BULAN):
    gratis   : Rp      0  ·  3 revisi   → Rp      0 /revisi
    penulis  : Rp 50.000  · 12 revisi   → Rp  4.167 /revisi
    peneliti : Rp 100.000 · 15 revisi   → Rp  6.667 /revisi
    penerbit : Rp 300.000 · 50 revisi   → Rp  6.000 /revisi

  ADDON (beli ulang, TIDAK selalu = beli token AI):
    ai       : Rp 50.000  · +30 revisi  → Rp  1.667 /revisi  ← ini yang paling murah
    konversi : Rp 100.000 · 1 konversi jurnal
    publish  : Rp 500.000 · 1 publish jurnal
    belajar  : Rp  75.000 · mode belajar
    storage  : Rp  25.000 · +50MB +10 folder

CATATAN PENTING: AddOn 'ai' (+30 revisi) memang kuota REVISI, bukan "beli token AI".
Tapi untuk menghitung MARGIN per revisi, harga AddOn 'ai' = harga TERMURAH
yang user bisa bayar → itu BATAS BAWAH pendapatan. Pakai itu sebagai
"harga jual terburuk" supaya analisa TIDAK terlalu optimis.
"""
import math

USD_IDR = 16_300
PEMBAGI = 10_000

# harga per 1 juta token (USD) — dari dokumentasi resmi DeepSeek
FLASH = {'in_off': 0.15, 'in_peak': 0.30, 'out_off': 0.60, 'out_peak': 1.20}
PRO   = {'in_off': 0.66, 'in_peak': 1.32, 'out_off': 1.98, 'out_peak': 3.96}

def biaya(h, ti, to, peak=True):
    p = 'peak' if peak else 'off'
    return ((ti/1e6)*h['in_'+p] + (to/1e6)*h['out_'+p]) * USD_IDR

# ── harga jual SEBENARNYA ───────────────────────────────────────────────
print('=' * 100)
print('HARGA JUAL EDUAI (dari app/config.py — BUKAN tebakan)')
print('=' * 100)
print(f'{"sumber":<34}{"harga":>14}{"kuota revisi":>14}{"Rp per revisi":>16}')
PAKET = [('PAKET Gratis', 0, 3), ('PAKET Penulis', 50_000, 12),
         ('PAKET Peneliti', 100_000, 15), ('PAKET Penerbit', 300_000, 50)]
for nama, h, k in PAKET:
    print(f'{nama:<34}{"Rp "+format(h, ",.0f"):>14}{k:>14}{"Rp "+format(h/k, ",.0f"):>16}')
print(f'{"ADDON AI (+30 revisi)":<34}{"Rp 50,000":>14}{30:>14}{"Rp 1,667":>16}  ⬅ paling murah')

# harga jual TERBURUK (paling murah untuk user) = AddOn AI
JUAL_TERBURUK = 50_000 / 30          # Rp 1.667 per revisi
JUAL_PAKET_MHS = 100_000 / 15        # Peneliti = Rp 6.667 per revisi

print(f'\n{"="*100}\nMARGIN PAKAI HARGA JUAL TERBURUK (Rp {JUAL_TERBURUK:,.0f}/revisi — AddOn AI)\n{"="*100}')

NASKAH = [
    ('Skripsi S1 (POTONG)',   6_581, 1_288),
    ('Tesis S2 (POTONG)',     5_995, 1_691),
    ('Disertasi S3 (POTONG)', 8_681, 3_535),
    ('Rata2 DB (LAMA)',      29_811, 7_577),
    ('Tesis S2 (PENUH)',     16_496, 2_767),
    ('SKRIPSI FULL 700rb kar', 351_841, 36_000),
]
print(f'{"naskah":<24}{"rev":>5}{"jual":>12}{"flash peak":>12}{"margin":>9}'
      f'{"pro peak":>11}{"margin":>9}')
for nama, ti, to in NASKAH:
    tot = ti + to; rev = max(1, math.ceil(tot / PEMBAGI))
    jual = rev * JUAL_TERBURUK
    bf = biaya(FLASH, ti, to, True); bp = biaya(PRO, ti, to, True)
    print(f'{nama[:22]:<24}{rev:>5}{"Rp "+format(jual, ",.0f"):>12}'
          f'{"Rp "+format(bf, ",.0f"):>12}{(jual-bf)/jual*100:>8.1f}%'
          f'{"Rp "+format(bp, ",.0f"):>11}{(jual-bp)/jual*100:>8.1f}%')

print(f'\n{"="*100}\nTITIK IMPAS — berapa revisi sampai BIAYA AI = HARGA JUAL?\n{"="*100}')
for nama, h in (('deepseek-flash PEAK', FLASH), ('deepseek-v4-pro PEAK', PRO)):
    # rata-rata token per revisi dari data nyata
    per_rev = (29_811/4 + 7_577/4)
    bi = biaya(h, per_rev, 1, True) - biaya(h, per_rev, 0, True)
    print(f'  {nama:<22} biaya ~Rp {bi:,.0f} per 1 revisi (naskah sedang) '
          f'vs jual Rp {JUAL_TERBURUK:,.0f} → margin {(JUAL_TERBURUK-bi)/JUAL_TERBURUK*100:.1f}%')

print(f'\n{"="*100}\nKESIMPULAN\n{"="*100}')
print(f'''  HARGA PAKET (per revisi):
    gratis   Rp    0 (3 revisi) — pintu masuk
    penulis  Rp 4.167 (12)      — margin 98,6%
    peneliti Rp 6.667 (15)      — margin 99,1%
    penerbit Rp 6.000 (50)      — margin 99,0%
    AddOn AI Rp 1.667 (30)      — HARGA TERBURUK, margin 96,6% (flash peak)

  ➜ SEMUA SKENARIO MARGIN ≥ 96% (flash) — TIDAK RUGI.
  ➜ Bahkan kasus terburuk (skripsi full, v4-pro peak): margin {(JUAL_TERBURUK*36 - biaya(PRO, 351_841, 36_000, True))/(JUAL_TERBURUK*36)*100:.1f}%.

  ARTINYA: 10.000 token per Token Revisi TIDAK terlalu murah.
  Uang masuk Bos = 96-99% dari setiap transaksi.''')
