"""Ambil peta_json tersimpan file 126 dari DB live (BACA SAJA, read-only).

Jalan di dalam container eduai-app:
  docker cp ambil_peta126.py eduai-app:/tmp/ambil_peta126.py
  docker exec eduai-app python3 /tmp/ambil_peta126.py
  docker cp eduai-app:/tmp/peta126.json /tmp/peta126.json
Tulis /tmp/peta126.json + /tmp/peta126_meta.txt di container.
"""
import json
import sqlite3

con = sqlite3.connect('file:/app/data/eduai.db?mode=ro', uri=True)
row = con.execute(
    "SELECT peta_json, peta_dibuat, peta_sidik FROM profil_dokumen "
    "WHERE file_id = 126 AND user_id = 12").fetchone()
if not row or not row[0]:
    print('TIDAK ADA')
    raise SystemExit(1)
with open('/tmp/peta126.json', 'w', encoding='utf-8') as f:
    f.write(row[0])
with open('/tmp/peta126_meta.txt', 'w', encoding='utf-8') as f:
    f.write('peta_dibuat=%s\npeta_sidik=%s\npanjang=%d\n'
            % (row[1], row[2], len(row[0])))
print('OK panjang=%d dibuat=%s' % (len(row[0]), row[1]))
