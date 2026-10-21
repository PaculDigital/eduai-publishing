"""ANALISA HARGA v2 — pakai HARGA PROVIDER ASLI (DeepSeek resmi), bukan harga farming.

SUMBER RESMI (api-docs.deepseek.com/quick_start/pricing, diambil 24Sep26):
  MODEL              : deepseek-flash (DeepSeek-V4.1-Flash)  |  deepseek-v4-pro
  1M INPUT (cache hit): $0.003 off-peak / $0.006 peak        |  $0.022 / $0.044
  1M INPUT (cache miss): $0.15  off-peak / $0.30  peak       |  $0.66  / $1.32
  1M OUTPUT           : $0.60  off-peak / $1.20  peak        |  $1.98  / $3.96
  Off-peak = SETENGAH peak. Peak = 01:00-04:00 & 06:00-10:00 UTC Sen-Jum.

CATATAN: WIB (UTC+7) → peak 08.00-11.00 & 13.00-17.00 WIB. Sisanya off-peak.
Itu JAM KERJA MAHASISWA — jadi banyak yang kena tarif PEAK. Hitung dua-duanya.
"""
import math

USD_IDR = 16_300          # kurs konservatif (per 24Sep26)
PEMBAGI = 10_000

# harga per 1 JUTA token (USD)
HARGA = {
    'deepseek-flash': {
        'in_miss_off': 0.15, 'in_miss_peak': 0.30,
        'in_hit_off': 0.003, 'in_hit_peak': 0.006,
        'out_off': 0.60,     'out_peak': 1.20,
    },
    'deepseek-v4-pro': {
        'in_miss_off': 0.66, 'in_miss_peak': 1.32,
        'in_hit_off': 0.022, 'in_hit_peak': 0.044,
        'out_off': 1.98,     'out_peak': 3.96,
    },
}

def biaya(model, tok_in, tok_out, peak=False, cache_hit=False):
    h = HARGA[model]
    p = 'peak' if peak else 'off'
    k_in = ('in_hit_' if cache_hit else 'in_miss_') + p
    return (tok_in / 1e6) * h[k_in] + (tok_out / 1e6) * h['out_' + p]

# ── naskah nyata: rata-rata DB + hasil uji hari ini ─────────────────────
NASKAH = [
    ('Rata2 DB (cara LAMA)', 29_811, 7_577),
    ('Tesis S2 (POTONG)',     5_995, 1_691),
    ('Skripsi S1 (POTONG)',   6_581, 1_288),
    ('Disertasi S3 (POTONG)', 8_681, 3_535),
    ('Tesis S2 (PENUH)',     16_496, 2_767),
    ('Skripsi S1 (PENUH)',   18_497, 2_428),
]

print('=' * 100)
print('ANALISA v2 — HARGA PROVIDER ASLI (DeepSeek resmi), kurs Rp %s/USD' % f'{USD_IDR:,}')
print('=' * 100)
print(f'{"naskah":<22}{"tok_in":>8}{"tok_out":>8}{"tok":>9}{"rev":>4}'
      f'{"OFF-PEAK flash":>17}{"PEAK flash":>14}{"Rp/1 rev (peak)":>17}')
for nama, ti, to in NASKAH:
    tot = ti + to; rev = max(1, math.ceil(tot / PEMBAGI))
    off = biaya('deepseek-flash', ti, to, peak=False) * USD_IDR
    pk = biaya('deepseek-flash', ti, to, peak=True) * USD_IDR
    print(f'{nama[:20]:<22}{ti:>8,}{to:>8,}{tot:>9,}{rev:>4}'
          f'{"Rp "+format(off, ",.0f"):>17}{"Rp "+format(pk, ",.0f"):>14}'
          f'{"Rp "+format(pk/rev, ",.0f"):>17}')

print(f'\n{"─"*100}\nBANDINGKAN DENGAN HARGA YANG WULAN PAKAI TADI (SALAH)\n{"─"*100}')
ti, to = 6_581, 1_288; tot = ti + to
print(f'  Tarif tadi (farming/diskon): Rp 0,0155915/token → Rp {(tot*0.0155915):,.0f}')
pk = biaya('deepseek-flash', ti, to, peak=True) * USD_IDR
off = biaya('deepseek-flash', ti, to, peak=False) * USD_IDR
print(f'  HARGA ASLI peak           : Rp {pk:,.0f}  → {pk/(tot*0.0155915):.1f}× LEBIH MAHAL')
print(f'  HARGA ASLI off-peak       : Rp {off:,.0f}  → {off/(tot*0.0155915):.1f}× lebih mahal')
print(f'  HARGA ASLI v4-pro peak    : Rp {biaya("deepseek-v4-pro", ti, to, True)*USD_IDR:,.0f}')

print(f'\n{"─"*100}\nMARGIN DENGAN HARGA ASLI — AddOn +30 Token = Rp 50.000 (Rp 1.667/Token)\n{"─"*100}')
print(f'{"naskah":<22}{"rev":>4}{"jual":>12}{"biaya peak":>13}{"biaya off":>12}'
      f'{"margin peak":>13}{"margin off":>12}')
for nama, ti, to in NASKAH:
    tot = ti + to; rev = max(1, math.ceil(tot / PEMBAGI))
    jual = rev * 50_000 / 30
    pk = biaya('deepseek-flash', ti, to, peak=True) * USD_IDR
    off = biaya('deepseek-flash', ti, to, peak=False) * USD_IDR
    mp = (jual - pk) / jual * 100; mo = (jual - off) / jual * 100
    print(f'{nama[:20]:<22}{rev:>4}{"Rp "+format(jual, ",.0f"):>12}'
          f'{"Rp "+format(pk, ",.0f"):>13}{"Rp "+format(off, ",.0f"):>12}'
          f'{mp:>12.1f}%{mo:>11.1f}%')

print(f'\n{"─"*100}\nKASUS PALING BURUK — SKRIPSI FULL (700.599 kar, 36 Token per §4.13)\n{"─"*100}')
T_IN, T_OUT = 351_841, 36_000
for m in ('deepseek-flash', 'deepseek-v4-pro'):
    for peak in (True, False):
        b = biaya(m, T_IN, T_OUT, peak=peak) * USD_IDR
        jual = 36 * 50_000 / 30
        print(f'  {m:<16}{"PEAK  " if peak else "OFF   "}biaya Rp {b:>10,.0f} · jual Rp {jual:,.0f} '
              f'· margin {(jual-b)/jual*100:>5.1f}%')

print(f'\n{"─"*100}\nKALAU TARIF TURUN: berapa agar margin tetap ≥90% pada kasus PALING BURUK?\n{"─"*100}')
b_worst = biaya('deepseek-v4-pro', T_IN, T_OUT, peak=True) * USD_IDR
print(f'  Biaya kasus terburuk (v4-pro PEAK) = Rp {b_worst:,.0f}')
for target in (0.90, 0.93, 0.95):
    harga_per_token = b_worst / ((1 - target) * 36)
    rp_per_10k = harga_per_token * PEMBAGI
    print(f'  agar margin {target*100:.0f}% → 1 Token Revisi harus dijual Rp {harga_per_token:,.0f} '
          f'(sekarang Rp 1.667) → setara Rp {rp_per_10k:,.0f} per 10.000 token')
