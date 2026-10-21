"""HITUNG TARIF KUOTA REVISI — berbasis BIAYA NYATA, bukan tebakan.

Pertanyaan Bos: sekali revisi potong berapa token? Masih 60.000 karakter?
Atau ditentukan ulang per skenario?

Metode: hitung biaya modal (Rp) tiap skenario revisi, lalu petakan ke kuota
supaya margin sehat + adil ke user.
"""
import json, subprocess, os

# --- TARIF TERUKUR (15Sep26) ---
USD_PER_TOKEN = 0.005878 / 6032      # dari uji nyata: 6.032 in + 426 out = $0.005878
USD_IDR = 16000                      # kurs asumsi (Bos bisa koreksi)
RUPIAH_PER_TOKEN = USD_PER_TOKEN * USD_IDR

KAR_PER_TOKEN = 2540 / 426           # dari uji: 25.400 kar -> 6.032 token ≈ 4,2 kar/token... 
# lebih tepat pakai rasio dokumen nyata: 111 kar per KB docx (terukur)
KAR_PER_TOKEN_NYATA = 6032 / 25400   # 0.2375 token per karakter in

def biaya(kar_in, kar_out):
    """Hitung biaya modal Rp dari karakter masuk & keluar."""
    tok_in = kar_in * 0.2375
    tok_out = kar_out * 0.30          # output ~3,3 kar/token
    total = (tok_in + tok_out) * RUPIAH_PER_TOKEN
    return tok_in, tok_out, total

print('=' * 78)
print('  TARIF: Rp {:.7f} per token  (kurs Rp {:,}/USD)'.format(RUPIAH_PER_TOKEN, USD_IDR))
print('=' * 78)

# ==== SKENARIO REVISI ====
skenario = [
    # nama,                         kar_in,  kar_out, keterangan
    ('1 paragraf (EYD/kalimat)',      1200,     500,  'konteks 400 + paragraf 800'),
    ('1 sub-bab (1.2 perkaya)',       6000,    3500,  'sub-bab 5rb + brief 1rb'),
    ('1 bab penuh (BAB III)',        40000,   12000,  'bab 40rb + brief + tetangga'),
    ('2 bab sekaligus',              80000,   24000,  'dua bab + brief'),
    ('seluruh dokumen (tesis 5 bab)',200000,   60000,  'proposal 5 bab utuh'),
    ('naskah 5 MB penuh',            568000,  120000, 'maksimum batas unggah'),
]

print()
print(f"{'SKENARIO':<30} {'kar in':>9} {'kar out':>8} {'tok in':>9} {'tok out':>8} {'BIAYA Rp':>10}")
print('-' * 78)
for nama, ki, ko, ket in skenario:
    ti, to, rp = biaya(ki, ko)
    print(f'{nama:<30} {ki:>9,} {ko:>8,} {ti:>9,.0f} {to:>8,.0f} {rp:>10,.0f}')

print()
print('=' * 78)
print('  PEMETAAN KE KUOTA (1 kuota = bagian dari harga paket)')
print('=' * 78)
print()
print('Harga paket Penulis Rp 50.000 = 12 kuota → 1 kuota ≈ Rp 4.167')
print()

paket = {
    'Penulis  (Rp 50.000/12 kuota)':  50000/12,
    'Peneliti (Rp 160.000/15 kuota)': 160000/15,
    'Penerbit (Rp 500.000/50 kuota)': 500000/50,
}
print(f"{'SKENARIO':<30} {'BIAYA Rp':>9} | {'Kuota':>5} {'Nilai Rp':>9} {'Margin':>8}")
print('-' * 78)
for nama, ki, ko, ket in skenario:
    ti, to, rp = biaya(ki, ko)
    # tentukan kuota
    if rp < 100:      k = 1
    elif rp < 500:    k = 1
    elif rp < 1500:   k = 1
    elif rp < 3000:   k = 2
    elif rp < 6000:   k = 3
    elif rp < 10000:  k = 4
    else:             k = 5
    nilai = k * (50000/12)
    margin = (nilai - rp) / nilai * 100 if nilai else 0
    print(f'{nama:<30} {rp:>9,.0f} | {k:>5} {nilai:>9,.0f} {margin:>7.1f}%')

print()
print('=' * 78)
print('  PERTANYAAN: berapa karakter layak dibaca untuk 1 KUOTA?')
print('=' * 78)
print()
for harga, kuota, nm in [(50000,12,'Penulis'), (160000,15,'Peneliti'), (500000,50,'Penerbit')]:
    per_kuota = harga/kuota
    # cari kar_in maks supaya biaya = 30% dari nilai kuota (margin 70%)
    target = per_kuota * 0.30
    # biaya(kar, kar*0.3) = target  -> approx
    # tok = kar*0.2375 + kar*0.3*0.30 ; rp = tok * RUPIAH_PER_TOKEN
    kar = target / ((0.2375 + 0.09) * RUPIAH_PER_TOKEN)
    print(f'{nm:<10} 1 kuota = Rp {per_kuota:>8,.0f} | margin-70% → aman baca ~{kar:>10,.0f} kar')
