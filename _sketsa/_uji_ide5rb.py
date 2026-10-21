"""UJI IDE BOS: kelipatan 5.000 token (in + out) = 1 kuota revisi.

Pakai DATA UJI NYATA dari 2 dokumen Bos.
Pertanyaan: apakah ide ini masuk akal? Berapa kuota keluar untuk
  (a) per bab  (b) 3 bab  (c) full 5 bab
"""

TARIF = 0.0155915
HARGA_PENULIS = 50000; KUOTA_PENULIS = 12
NILAI_1_KUOTA = HARGA_PENULIS/KUOTA_PENULIS     # Rp 4.167

# ── Data uji NYATA ──
UJI = [
    ('Tesis 3bab: BAB I (22.333 kar)',      5035,  636),
    ('Tesis 3bab: SELURUH (63.797 kar)',   15823, 1916),
    ('Skripsi: potongan 1 (55.000 kar)',   25596, 1979),
    ('Skripsi: potongan 1+2 (110.000 kar)',43389, 1657),
]
# Rasio konservatif untuk proyeksi
RASIO_IN  = 0.465     # token/karakter (tertinggi terukur)
RASIO_OUT = 0.08      # output ~8% dari input

print('='*90)
print('  UJI IDE BOS: kelipatan 5.000 token (in+out) = 1 kuota')
print('='*90)
print()
print('── A. DATA UJI NYATA, dipetakan ke ide Bos ──')
print()
print(f"{'UJI':<36} {'in':>7} {'out':>6} {'total':>7} {'5rb':>5} {'BIAYA':>9} {'NILAI':>9} {'MARGIN':>8}")
print('-'*90)
for n,i,o in UJI:
    tot = i+o
    kuota = max(1, -(-tot//5000))          # ceil(total/5000)
    rp = tot*TARIF
    nilai = kuota*NILAI_1_KUOTA
    m = (nilai-rp)/nilai*100
    print(f'{n:<36} {i:>7,} {o:>6,} {tot:>7,} {kuota:>5} {("Rp "+format(round(rp),",d")):>9} '
          f'{("Rp "+format(round(nilai),",d")):>9} {m:>7.1f}%')

print()
print('='*90)
print('  B. PROYEKSI PER BAB / 3 BAB / FULL 5 BAB (pakai rasio 0,465)')
print('='*90)
print()

def hit(kar, nama):
    ti = kar*RASIO_IN
    to = ti*RASIO_OUT
    tot = ti+to
    kuota = max(1, -(-tot//5000))
    rp = tot*TARIF
    nilai = kuota*NILAI_1_KUOTA
    m = (nilai-rp)/nilai*100
    print(f'{nama:<40} {tot:>9,.0f} tok  {kuota:>4} kuota  '
          f'Rp {rp:>7,.0f}  nilai Rp {nilai:>8,.0f}  margin {m:>5.1f}%')
    return kuota

print('── SKRIPSI FULL (700.599 kar, BAB I–V) ──')
print()
n1 = hit(140000, '  1 bab rata-rata (700rb/5)')
n3 = hit(420000, '  3 bab (BAB I+II+III)')
n5 = hit(700599, '  FULL 5 bab (seluruh skripsi)')
print()
print('── TESIS 3 BAB (63.797 kar) ──')
print()
t1 = hit(21300, '  BAB I saja')
t3 = hit(63797, '  ketiga bab sekaligus')
print()
print('── BATAS BARU 15 MB (teks maksimum ~1,5 juta kar) ──')
print()
b1 = hit(1500000, '  seluruh teks')
print()
print('='*90)
print('  C. CEK KEADILAN: apakah user "nakal" bisa merugikan?')
print('='*90)
print()
print('Paket Penulis: Rp 50.000 = 12 kuota. Kalau user pakai 12 kuota untuk')
print('skripsi FULL 5 bab terus-menerus (kasus terburuk):')
tot = 700599*RASIO_IN*1.08
kuota_per = -(-tot//5000)
rp_per = tot*TARIF
print(f'  1× skripsi full  = {kuota_per} kuota (biaya modal Rp {rp_per:,.0f})')
print(f'  12 kuota habis dalam {12/kuota_per:.1f}× operasi')
print(f'  Total biaya modal 12 kuota = Rp {rp_per*12:,.0f} vs harga Rp 50.000')
m = (50000-rp_per*12)/50000*100
print(f'  → MARGIN PAKET = {m:.1f}%  {"✅ AMAN" if m>50 else "⚠️ PERIKSA"}')
