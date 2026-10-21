#!/usr/bin/env bash
# Cek DATA NYATA: berapa catatan pembimbing yang punya sorotan, dan /
# apakah halaman /tinjau betul-betul hidup di produksi.
cd /opt/data/services/eduai-publishing || exit 1

echo "=== 1. Kolom & isi catatan_pembimbing ==="
docker exec eduai-app python3 -c "
import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
kol = [r[1] for r in c.execute('PRAGMA table_info(catatan_pembimbing)')]
print('  kolom:', kol)
print()
print('  jumlah baris:', c.execute('select count(*) from catatan_pembimbing').fetchone()[0])
# cek kolom sorotan
for k in ['teks_asli','awal','akhir','keadaan','posisi']:
    if k in kol:
        n = c.execute(f'select count(*) from catatan_pembimbing where \"{k}\" is not null and \"{k}\" != \"\"').fetchone()[0]
        print(f'  {k:12} terisi: {n}')
print()
rows = c.execute('select id, id_pembimbingan, substr(coalesce(teks_asli,\"\"),1,50), keadaan from catatan_pembimbing order by id desc limit 6').fetchall()
print('  contoh terakhir:')
for r in rows:
    print('   ', r)
" 2>&1 | head -25

echo
echo "=== 2. pembimbingan aktif ==="
docker exec eduai-app python3 -c "
import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
n = c.execute('select count(*) from pembimbingan').fetchone()[0]
print('  total pembimbingan:', n)
rows = c.execute('select id, nama_pembimbing, status, dibuat from pembimbingan order by id desc limit 5').fetchall()
for r in rows: print('   ', r)
" 2>&1 | head -10

echo
echo "=== 3. Halaman /tinjau hidup? (cek rute + token contoh) ==="
docker exec eduai-app python3 -c "
from app.main import app
r = [x.path for x in app.routes if hasattr(x,'path') and 'tinjau' in x.path]
print('  rute tinjau:', sorted(set(r)))
"
curl -s -o /dev/null -w '  /tinjau/token-palsu -> HTTP %{http_code}\n' --max-time 15 https://eduai.bikinaja.id/tinjau/token-palsu
