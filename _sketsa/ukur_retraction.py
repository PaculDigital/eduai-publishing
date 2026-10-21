"""UKUR: berapa artikel hasil pencarian EduAi yang DITARIK (retracted)?

Pakai Scopus yang SUDAH kita punya (kunci di .env).
Cek: apakah judul/docstring mengandung 'retract' / 'withdrawn'.
Jalankan DI DALAM container: docker exec -w /app eduai-app python3 _ukur_retraction.py
"""
import sys
import time

sys.path.insert(0, '/app')
from app.pustaka import cari_scopus, cari_semua, kata_kunci     # noqa: E402

TEMA = [
    'aktivitas fisik siklus menstruasi',
    'keputusan pembelian kualitas produk',
    'kepuasan kerja kinerja karyawan',
    'motivasi minat belajar',
    'literasi digital hasil belajar',
    'kepemimpinan kinerja karyawan',
]

KATA = ('retract', 'withdraw', 'pulled', 'ditarik', 'dibatalkan')

print('UKUR RETRACTION — pakai Scopus (kunci kita)')
print('=' * 72)
t0 = time.time()
jml, ada_tanda, sitasi_besar = 0, 0, 0
contoh = []
for tema in TEMA:
    kw = kata_kunci(tema)
    hasil = cari_scopus(kw['en'], query_siap=kw.get('q_scopus', ''))
    print('\nTEMA: %s → %d hasil Scopus' % (tema, len(hasil)))
    for a in hasil:
        judul = (a.get('title') or '')
        abstrak = (a.get('abstract') or '')
        teks = (judul + ' ' + abstrak).lower()
        jml += 1
        if any(k in teks for k in KATA):
            ada_tanda += 1
            if len(contoh) < 8:
                contoh.append((a.get('source'), judul[:60], a.get('year'),
                               a.get('cited_by_count')))
        if (a.get('cited_by_count') or 0) > 500:
            sitasi_besar += 1

print('\n%s' % '=' * 72)
print('RINGKASAN')
print('  artikel Scopus diperiksa   : %d' % jml)
print('  memuat kata retract/withdraw: %d (%.1f%%)' % (
    ada_tanda, (ada_tanda / jml * 100) if jml else 0))
print('  sitasi > 500 (artikel besar): %d' % sitasi_besar)
print('  waktu: %.1f dtk' % (time.time() - t0))
if contoh:
    print('\nCONTOH yang bertanda:')
    for s, j, y, c in contoh:
        print('  [%s] %s (%s) sitasi %s' % (s, j, y, c))
