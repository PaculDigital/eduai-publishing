"""BANDINGKAN PEMBAGI: 5rb / 10rb / 15rb / 25rb token = 1 Token Revisi.

Pakai DATA UJI NYATA dari 2 dokumen Bos.
Fokus: angka yang TERLIHAT USER di layar (harus wajar).
"""

TARIF = 0.0155915
NILAI_1_TOKEN_REVISI = 50000/12     # Rp 4.167

# ── Token NYATA dari uji ──
UJI = [
    ('Perbaiki 1 paragraf',           300),
    ('Perbaiki 1 sub-bab',           1500),
    ('Tesis: BAB I',                 5671),
    ('Tesis: SELURUH 3 bab',        17739),
    ('Skripsi: potongan 1 (55rb)',  27575),
    ('Skripsi: potongan 1+2',       45046),
]
# Proyeksi (rasio nyata 0,465 in + 8% out = 0,5022 token/kar)
PROY = [
    ('Tesis FULL 5 bab (~110rb kar)', 55240),
    ('Skripsi 1 bab (~140rb kar)',    70308),
    ('Skripsi 3 bab (~420rb kar)',   210924),
    ('Skripsi FULL (~700rb kar)',    351841),
]

def tampil(tok, bagi):
    n = tok/bagi
    return max(1, int(n if n == int(n) else int(n)+1))

print('='*94)
print('  PERBANDINGAN PEMBAGI — angka yang TERLIHAT USER di layar')
print('='*94)
print()

PEMBAGI = [5000, 10000, 15000, 25000]
hdr = f"{'OPERASI':<34} {'token AI':>10}" + ''.join(f'{b//1000}rb'.rjust(9) for b in PEMBAGI)
print(hdr)
print('-'*94)
for nama, tok in UJI + PROY:
    baris = f'{nama:<34} {tok:>10,}'
    for b in PEMBAGI:
        baris += f'{tampil(tok,b):>9}'
    print(baris)

print()
print('='*94)
print('  ISI KEUANGAN PER PEMBAGI (pakai skripsi FULL 351.841 token)')
print('='*94)
print()
print(f"{'PEMBAGI':<12} {'Token Revisi':>13} {'Nilai Rp':>12} {'Biaya AI':>10} {'MARGIN':>9} {'PAKET YG CUKUP':>20}")
print('-'*94)
biaya_ai = 351841*TARIF
paket = [('Gratis',3),('Penulis',12),('Peneliti',15),('Penerbit',50)]
for b in PEMBAGI:
    n = tampil(351841, b)
    nilai = n*NILAI_1_TOKEN_REVISI
    m = (nilai-biaya_ai)/nilai*100
    cukup = [f'{p}({k})' for p,k in paket if k>=n]
    ket = cukup[0] if cukup else 'TIDAK ADA → AddOn'
    print(f'{str(b)+" tok":<12} {n:>13} {("Rp "+format(int(nilai),",d")):>12} '
          f'{("Rp "+format(int(biaya_ai),",d")):>10} {m:>8.1f}% {ket:>20}')

print()
print('='*94)
print('  CEK KESEHATAN: apakah user masih TERPAKSA beli AddOn? (inti bisnis)')
print('='*94)
print()
for b in PEMBAGI:
    n_full = tampil(351841, b)
    n_1bab = tampil(70308, b)
    print(f'  {str(b)+" tok":<10} skripsi FULL = {n_full:>3} Token Revisi | '
          f'1 bab = {n_1bab:>2} | '
          f'paket Penulis(12) cukup? {"YA ✅" if n_full<=12 else "TIDAK → beli AddOn 💰"}')
