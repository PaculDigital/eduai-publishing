#!/usr/bin/env bash
# CEK FITUR SOROT PEMBIMBING — masih hidup?
# 1. Mesin sorotan (cari_sorotan / periksa_semua) jalan?
# 2. Halaman /tinjau/{token} ada & memuat UI sorotan?
# 3. Berapa catatan yang PUNYA sorotan di DB?
cd /opt/data/services/eduai-publishing || exit 1

echo "=== 1. MESIN SOROTAN — uji fungsi sungguhan di container ==="
docker exec eduai-app python3 -c "
from app import sorotan

naskah = '''Bab I Pendahuluan

Penelitian ini bertujuan menganalisis pengaruh digital marketing terhadap keputusan pembelian pada UMKM di Kota Makassar. Data dikumpulkan melalui kuesioner.

Rumusan masalah dalam penelitian ini adalah apakah digital marketing berpengaruh signifikan.'''

catatan = [
    {'id': 1, 'teks_asli': 'Penelitian ini bertujuan menganalisis pengaruh digital marketing terhadap keputusan pembelian'},
    {'id': 2, 'teks_asli': 'kalimat yang tidak ada sama sekali di naskah'},
]
hasil = sorotan.periksa_semua(naskah, catatan)
print('  periksa_semua ->', hasil if not isinstance(hasil, dict) else {k: v for k, v in list(hasil.items())[:6]})
print()
# coba satu per satu
for c in catatan:
    h = sorotan.cari_sorotan(naskah, c['teks_asli'])
    print('  catatan', c['id'], '->', {k: h[k] for k in list(h)[:5]})
"

echo
echo "=== 2. DB: catatan pembimbing yang PUNYA sorotan ==="
docker exec eduai-app python3 -c "
import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
# cari tabel catatan pembimbing
t = [r[0] for r in c.execute(\"select name from sqlite_master where type='table'\")]
print('  tabel terkait:', [x for x in t if 'catatan' in x or 'bimbing' in x or 'tinjau' in x])
"

echo
echo "=== 3. Halaman /tinjau/{token} — UI sorotan ada? ==="
grep -c 'sorot' app/templates/tinjau.html
echo "   (jumlah kemunculan kata 'sorot' di tinjau.html di atas)"
grep -n 'klik\|Klik' app/templates/tinjau.html | head -6
