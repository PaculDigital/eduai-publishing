"""Cek: apakah ada berkas format LAMA Office (.doc/.xls/.ppt) di storage user?

Kalau ADA ⇒ larangan baru bisa mengunci user dari berkasnya sendiri (perlu jalan keluar).
"""
import sqlite3

db = sqlite3.connect('/app/data/eduai.db')
total = db.execute('select count(*) from files').fetchone()[0]
print('total berkas:', total)
for pola in ('%.doc', '%.xls', '%.ppt', '%.rtf', '%.odt', '%.zip'):
    n = db.execute('select count(*) from files where lower(nama) like ?',
                   (pola,)).fetchone()[0]
    print(f'  {pola}: {n}')
    if n:
        for r in db.execute(
                'select id, nama from files where lower(nama) like ? limit 5',
                (pola,)):
            print('       ·', r)
