"""ANALISA RISIKO: apa yang terjadi pada naskah 5 MB di alur revisi SEKARANG."""

AI_POTONG_KARAKTER = 55000
AI_POTONG_MAKS_BAGIAN = 6
AI_MAX_KOMENTAR = 10

print('=' * 80)
print('  SIMULASI: NASKAH 5 MB MASUK ALUR REVISI (kondisi SEKARANG)')
print('=' * 80)
print()
print('  Asumsi rasio nyata: 111 karakter per KB docx')
print()

for mb, ket in ((0.56, 'TESIS BOS (nyata)'), (2.1, 'skripsi (info Bos)'),
                (3.4, 'tesis (info Bos)'), (5.0, 'MAKS (batas baru)')):
    kar = mb * 111 * 1024
    bagian = max(1, min(-(-int(kar) // AI_POTONG_KARAKTER), AI_POTONG_MAKS_BAGIAN))
    print('  {:<20} {:>10,.0f} kar'.format(ket, kar))
    print('     bagian   : {}'.format(bagian))
    print('     kuota    : {} dari 3 (gratis) {}'.format(
        bagian, '<-- HABIS SEMUA' if bagian >= 3 else ''))
    if bagian >= AI_POTONG_MAKS_BAGIAN:
        print('     ⚠️  KENA CAP {} bagian -> SISA KARAKTER TIDAK DIPROSES!'.format(
            AI_POTONG_MAKS_BAGIAN))
        sisa = kar - AI_POTONG_MAKS_BAGIAN * AI_POTONG_KARAKTER
        print('     ⚠️  {:,} karakter ({:.1f}%) TIDAK tersentuh AI'.format(
            sisa, sisa / kar * 100))
    print()

print('=' * 80)
print('  TEMUAN KUNCI')
print('=' * 80)
print()
print('  1. AI_MAX_NASKAH (60.000) TIDAK DIPAKAI — hanya di-import, tidak dipanggil.')
print('     -> jadi AI TIDAK dibatasi 60.000 karakter. Angka itu MATI.')
print()
print('  2. Yang membatasi = AI_POTONG_KARAKTER (55.000) per bagian')
print('     + AI_POTONG_MAKS_BAGIAN (6) = batas keras.')
print()
kar5 = 5.0 * 111 * 1024
bagian5 = max(1, min(-(-int(kar5) // AI_POTONG_KARAKTER), AI_POTONG_MAKS_BAGIAN))
sisa5 = kar5 - AI_POTONG_MAKS_BAGIAN * AI_POTONG_KARAKTER
print('  3. NASKAH 5 MB -> kena CAP 6 bagian. Sisa {:,} kar ({:.0f}%) TIDAK diproses.'.format(
    sisa5, sisa5 / kar5 * 100))
print()
print('  +--------------------------------------------------------------+')
print('  |  KALAU user setuju 6 bagian:                                 |')
print('  |    - kuota gratis 3 -> TIDAK CUKUP (butuh 6) -> DITOLAK      |')
print('  |    - paket Penulis 12 -> CUKUP, tapi 6 kuota habis sekaligus |')
print('  |    - dan 38% naskah TETAP tidak diproses (cap 6)             |')
print('  +--------------------------------------------------------------+')
