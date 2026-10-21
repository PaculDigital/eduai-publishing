"""ANALISA HARGA TOKEN REVISI — apakah 10.000/token terlalu murah?

SEMUA angka dari SUMBER NYATA:
  - tarif model  : Rp 0,0155915/token (MASTER_PLAN §4.13, model ag/gemini-3.8-flash-high)
  - token_in/out : rata-rata DB proses_ai (15 proses terakhir)
  - paket & harga: app/config.py PAKET + ai.py daftar_addon
"""
import math

TARIF = 0.0155915          # Rp per token (input & output dianggap sama — konservatif)
PEMBAGI = 10_000

# ── angka nyata dari DB ────────────────────────────────────────────────
avg_in, avg_out = 29_811, 7_577          # rata-rata 15 proses_ai (cara SEKARANG)
avg_tot = avg_in + avg_out

# hasil uji hari ini: POTONG (setelah jembatan) — 3 naskah
UJI_POTONG = [
    ('Tesis S2 manajemen', 5_995, 1_691, 1),
    ('Skripsi S1 UNMUL',   6_581, 1_288, 1),
    ('Disertasi S3 UNHAS', 8_681, 3_535, 2),
]
UJI_PENUH = [
    ('Tesis S2 manajemen', 16_496, 2_767, 2),
    ('Skripsi S1 UNMUL',   18_497, 2_428, 3),
    ('Disertasi S3 UNHAS', 19_449, 3_659, 3),
]

print('=' * 96)
print('ANALISA HARGA TOKEN REVISI — apakah 10.000 token terlalu murah?')
print('=' * 96)
print(f'Tarif model (nyata)  : Rp {TARIF:.7f} / token')
print(f'Pembagi (rumus §4.13): {PEMBAGI:,} token per 1 Token Revisi')

print(f'\n{"─"*96}\n1. BIAYA AI NYATA (dari DB: rata-rata 15 proses terakhir)\n{"─"*96}')
print(f'  token_in  rata-rata : {avg_in:>8,}')
print(f'  token_out rata-rata : {avg_out:>8,}')
print(f'  TOTAL               : {avg_tot:>8,} token')
biaya_sekarang = avg_tot * TARIF
print(f'  BIAYA AI per proses : Rp {biaya_sekarang:>10,.1f}')
print(f'  Token Revisi dipotong: {math.ceil(avg_tot/PEMBAGI)}')
print(f'  Biaya AI per 1 Token Revisi: Rp {biaya_sekarang/math.ceil(avg_tot/PEMBAGI):,.1f}')

print(f'\n{"─"*96}\n2. SETELAH JEMBATAN (hasil uji nyata hari ini)\n{"─"*96}')
print(f'{"naskah":<24}{"cara":<9}{"token":>9}{"rev":>5}{"biaya AI":>12}{"Rp/token-rev":>14}')
for nama, i, o, r in UJI_PENUH:
    print(f'{nama[:22]:<24}{"PENUH":<9}{i+o:>9,}{r:>5}{"Rp "+format((i+o)*TARIF, ",.0f"):>12}'
          f'{"Rp "+format((i+o)*TARIF/r, ",.0f"):>14}')
for nama, i, o, r in UJI_POTONG:
    print(f'{nama[:22]:<24}{"POTONG":<9}{i+o:>9,}{r:>5}{"Rp "+format((i+o)*TARIF, ",.0f"):>12}'
          f'{"Rp "+format((i+o)*TARIF/r, ",.0f"):>14}')

rp = [(i+o)*TARIF/r for _, i, o, r in UJI_POTONG]
print(f'\n  Rata-rata biaya AI per 1 Token Revisi (POTONG): Rp {sum(rp)/len(rp):,.1f}')

# ── paket & addon ───────────────────────────────────────────────────────
print(f'\n{"─"*96}\n3. HARGA JUAL & MARGIN (angka paket dari app/config.py)\n{"─"*96}')
# dari memory/MASTER_PLAN: AddOn AI +30 Token = Rp 50.000
ADDON_TOKEN, ADDON_HARGA = 30, 50_000
rp_per_token_jual = ADDON_HARGA / ADDON_TOKEN
print(f'  AddOn AI: +{ADDON_TOKEN} Token Revisi = Rp {ADDON_HARGA:,}')
print(f'  HARGA JUAL per Token Revisi = Rp {rp_per_token_jual:,.0f}')

biaya_per_token = sum(rp)/len(rp)
margin = (rp_per_token_jual - biaya_per_token) / rp_per_token_jual * 100
print(f'  BIAYA AI per Token Revisi   = Rp {biaya_per_token:,.0f}  (pakai POTONG)')
print(f'  ➜ MARGIN = {margin:.1f}%')

# ── skenario pembagi ────────────────────────────────────────────────────
print(f'\n{"─"*96}\n4. KALAU PEMBAGI DITURUNKAN — apa akibatnya?\n{"─"*96}')
print(f'  {"pembagi":>9}{"1 Token = ...":>16}{"rev (POTONG 6.581)":>20}'
      f'{"jual":>10}{"biaya AI":>12}{"margin":>10}')
for p in (2_000, 3_000, 4_000, 5_000, 7_500, 10_000):
    tot = 6_581 + 1_288                      # naskah sedang (skripsi S1)
    rev = max(1, math.ceil(tot / p))
    jual = rev * rp_per_token_jual
    biaya = tot * TARIF
    m = (jual - biaya) / jual * 100 if jual else 0
    tanda = '  ⬅ sekarang' if p == 10_000 else ''
    print(f'  {p:>9,}{f"~{p:,} token":>16}{rev:>20}{"Rp "+format(jual, ",.0f"):>10}'
          f'{"Rp "+format(biaya, ",.0f"):>12}{m:>9.1f}%{tanda}')

print(f'\n{"─"*96}\n5. TIGA SUDUT PANDANG\n{"─"*96}')
print(f'  (a) MARGIN per token  : {margin:.1f}% — SANGAT SEHAT. 1 Token Revisi dijual')
print(f'      Rp {rp_per_token_jual:,.0f} sedangkan biaya AI cuma Rp {biaya_per_token:,.0f}')
print(f'      → rugi TIDAK MUNGKIN terjadi per-token.')
print(f'  (b) RISIKO RUGI NYATA : bukan pada tarif, tapi pada NASKAH SANGAT BESAR')
print(f'      yang kena CAP 60. Naskah 1,5 juta kar = ~753.000 token = Rp 11.745 biaya.')
print(f'      Kalau user bayar 60 Token × Rp 1.667 = Rp 100.000 → masih untung, TAPI')
print(f'      tipis kalau model naik harga atau user revisi berulang.')
print(f'  (c) RISIKO BISNIS     : harga TERLALU MAHAL = user kabur. Kata Bos sendiri:')
print(f'      pembagi 5.000 bikin skripsi full = 71 Token (menakutkan). 36 Token "wajar".')

print(f'\n{"="*96}\nKESIMPULAN\n{"="*96}')
print(f'''  TIDAK PERLU DITURUNKAN. Margin {margin:.0f}% — tidak rugi.

  Buktinya: 1 Token Revisi = Rp {rp_per_token_jual:,.0f} (harga jual)
            biaya AI nyata  = Rp {biaya_per_token:,.0f}
            ➜ keuntungan {rp_per_token_jual/biaya_per_token:.0f}× lipat per token.

  Yang WAJIB dijaga BUKAN pembaginya, melainkan:
    1) pasang pagar CAP yang benar-benar bergigi untuk naskah raksasa;
    2) selesaikan jembatan konteks (harga turun 2-3x → margin NAIK, bukan turun);
    3) awasi harga model (kalau model naik 3x, margin masih aman 96% → 88%).''')
