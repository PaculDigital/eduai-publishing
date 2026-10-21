"""Baca daftar users di BEBERAPA berkas DB (cadangan vs produksi)."""
import sqlite3
import glob
import os

DAFTAR = [
    '_arsip/pre-c7-pascapagar-20260928/eduai.db',
    '_arsip/pra-sot/20260928_100404-sot/eduai.db',
    '_arsip/pre-c7uji-27sep/bak-c7.db',
    '_arsip/pre-bersih-keseluruhan-26Sep1638/SEBELUM.db',
]
DAFTAR += sorted(glob.glob('/opt/data/services/eduai-publishing/data/eduai.db'))

for f in DAFTAR:
    if not os.path.exists(f):
        print('tidak ada:', f)
        continue
    try:
        c = sqlite3.connect(f)
        rows = c.execute('SELECT id,email,paket FROM users ORDER BY id').fetchall()
        print(f, '→', rows)
        c.close()
    except Exception as e:
        print(f, 'GALAT', e)
