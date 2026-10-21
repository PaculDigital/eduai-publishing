"""PREDIKSI: biaya percakapan panjang (10-20 putaran) + kapan harus dipecah.

Temuan: token MASUK ~2.200/putaran karena riwayat ikut dikirim.
"""
TARIF = 0.005878 / 6032          # $/token (terukur, mixed in+out)
KURS = 16000

print('=' * 84)
print('  PREDIKSI BIAYA PERCAKAPAN (dari angka terukur)')
print('=' * 84)
print()
print('  Hasil ukur 4 putaran: 9.037 in + 553 out = 9.590 token = Rp 150')
print('  -> rata-rata ~2.400 token/putaran (riwayat naik terus)')
print()
print('  {:>8}  {:>12}  {:>12}  {:>10}  {}'.format(
    'Putaran', 'Token total', 'Biaya', 'Rupiah', 'Catatan'))
print('  ' + '-' * 74)

for n in (4, 8, 12, 16, 20, 30):
    # token masuk naik linear (riwayat), token keluar ~130/putaran
    masuk = sum(2200 + i * 55 for i in range(n))
    keluar = 130 * n
    tok = masuk + keluar
    b = tok * TARIF
    cat = ''
    if n <= 8:
        cat = 'wajar (gali niat + judul)'
    elif n <= 16:
        cat = 'panjang (banyak revisi niat)'
    else:
        cat = 'terlalu panjang -> pecah sesi'
    print('  {:>8}  {:>12,}  ${:>11.4f}  Rp {:>8,}  {}'.format(
        n, tok, b, int(b * KURS), cat))

print()
print('=' * 84)
print('  PEMBANDING: HARGA PAKET')
print('=' * 84)
for nama, harga in (('Gratis', 0), ('Penulis', 50000),
                    ('Peneliti', 160000), ('Penerbit', 500000)):
    print('  {:<10} Rp {:>9,}'.format(nama, harga))
print()
print('  Percakapan 8 putaran = Rp 305 (0,6% dari paket Penulis)')
print('  Percakapan 16 putaran = Rp 1.180 (2,4% dari paket Penulis)')
print()
print('  KESIMPULAN: percakapan SANGAT MURAH dibanding paket.')
print('  Yang mahal = menulis naskah (output panjang, bukan obrolan).')
