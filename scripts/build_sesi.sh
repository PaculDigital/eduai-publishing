#!/usr/bin/env bash
# Build + restart + (opsional) drop tabel sesi_edit karena skema berubah.
#
# KENAPA perlu drop: tabel sesi_edit sudah terlanjur dibuat dengan kolom
# DateTime TANPA timezone. `create_all` TIDAK mengubah tabel yang sudah ada,
# jadi skema lama tetap terpakai -> bug naive/aware berlanjut.
# Tabel ini hanya berisi sesi berjalan (data sementara), jadi aman di-drop;
# isinya dibangun ulang otomatis saat user membuka editor.
set -uo pipefail
cd /opt/data/services/eduai-publishing

echo "=== 1. Verifikasi kode ==="
/opt/data/.venv/bin/python3 scripts/verifikasi_sesi.py 2>&1 | tail -4 || exit 1

echo "=== 2. Build ==="
docker build -t eduai-app:v1 . 2>&1 | tail -2

echo "=== 3. Restart ==="
bash scripts/jalankan.sh 2>&1 | tail -1
sleep 14

echo "=== 4. Drop tabel sesi_edit (skema lama) ==="
docker exec eduai-app /usr/local/bin/python -c "
import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
t = [r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")]
if 'sesi_edit' in t:
    c.execute('DROP TABLE sesi_edit')
    c.commit()
    print('  tabel sesi_edit DROPPED (akan dibuat ulang saat startup)')
else:
    print('  tabel sesi_edit tidak ada (aman)')
c.close()
"

echo "=== 5. Restart ulang supaya tabel dibuat dengan skema baru ==="
bash scripts/jalankan.sh 2>&1 | tail -1
sleep 14

echo "=== 6. Verifikasi skema baru ==="
docker exec eduai-app /usr/local/bin/python -c "
import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
t = [r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")]
print('  tabel:', t)
if 'sesi_edit' in t:
    sql = c.execute(\"SELECT sql FROM sqlite_master WHERE name='sesi_edit'\").fetchone()[0]
    print('  skema:')
    for baris in sql.splitlines():
        print('   ', baris.strip())
c.close()
"

echo "=== 7. Health ==="
docker exec eduai-app /usr/local/bin/python -c "
import urllib.request
print(' ', urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=8).read().decode()[:80])
" 2>&1 | tail -2
