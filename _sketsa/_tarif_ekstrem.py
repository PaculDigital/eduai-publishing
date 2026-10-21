"""SKENARIO EKSTREM: apa yang terjadi kalau user 'nakal' atau boros?

Tujuan: pastikan tarif kuota AMAN walau user memaksimalkan (worst case).
"""

RUPIAH_PER_TOKEN = 0.0155915
NILAI_KUOTA = 50000 / 12     # Rp 4.167 (paket Penulis — paling ketat)

def biaya(kar_in, kar_out, ulang=1):
    tok = (kar_in * 0.2375 + kar_out * 0.30) * ulang
    return tok * RUPIAH_PER_TOKEN

print('=' * 82)
print('  WORST CASE: user memaksimalkan tiap rupiah yang dia bayar')
print('=' * 82)
print()
print('Paket Penulis Rp 50.000 = 12 kuota. Pertanyaan: kalau user "nakal",')
print('berapa maksimal biaya modal yang dia bisa timbulkan?')
print()

# Skenario nakal
kasus = [
    ('Rapi: 12x revisi 1 sub-bab',            6000,   3500, 12, 1),
    ('Sedang: 12x revisi 1 bab',             40000,  12000, 12, 1),
    ('Nakal: 12x baca seluruh tesis',       200000,  60000, 12, 1),
    ('Sangat nakal: 12x naskah 5 MB',       568000, 120000, 12, 1),
    ('Ekstrem: 12x 5MB + 5x ubah alur',     568000, 120000, 12, 5),
]

print(f"{'KASUS':<40} {'BIAYA MODAL':>13} {'HARGA':>9} {'MARGIN':>9}")
print('-' * 82)
for nama, ki, ko, kali, mult in kasus:
    if nama.startswith('Ekstrem'):
        rp = biaya(ki, ko, 12) + biaya(ki, ko, 5) * 4   # 5 kuota x 4 kali
    else:
        rp = biaya(ki, ko, kali)
    margin = (50000 - rp) / 50000 * 100
    tanda = '✅' if margin > 50 else ('⚠️' if margin > 0 else '🔴')
    print(f'{nama:<40} {rp:>12,.0f} {50000:>9,} {margin:>8.1f}% {tanda}')

print()
print('=' * 82)
print('  KESIMPULAN: 1 KUOTA = berapa karakter?')
print('=' * 82)
print()
# Cari titik aman: biaya = 40% dari nilai kuota (margin 60% — sangat sehat)
target = NILAI_KUOTA * 0.40
kar_aman = target / ((0.2375 + 0.09) * RUPIAH_PER_TOKEN)
print(f'Nilai 1 kuota          : Rp {NILAI_KUOTA:,.0f}')
print(f'Target biaya (40%)     : Rp {target:,.0f}   (margin 60% — sehat)')
print(f'→ AMAN baca            : {kar_aman:,.0f} karakter per kuota')
print()
print('Tapi ada BATAS ATAS praktis — jangan biarkan 1 kuota = seluruh naskah:')
for batas, ket in [(55000,'BATAS LAMA (sekarang)'), (120000,'usul: 1 bab + konteks'),
                   (200000,'usul: seluruh tesis proposal'), (60000,'60rb = angka lama?')]:
    rp = biaya(batas, batas*0.3)
    m = (NILAI_KUOTA - rp)/NILAI_KUOTA*100
    print(f'  {batas:>8,} kar  → biaya Rp {rp:>7,.0f}  margin {m:>5.1f}%   ({ket})')
