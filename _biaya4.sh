#!/bin/bash
# UKUR BIAYA NYATA — berapa biaya 1 revisi AI (naskah 55.000 kar)?
# Sumber: DB 9router + pemakaian token nyata dari tabel log.
docker cp 9router:/app/data/db/data.sqlite /tmp/9r.sqlite 2>/dev/null
docker cp 9router:/app/data/db/data.sqlite-wal /tmp/9r.sqlite-wal 2>/dev/null

python3 -c "
import sqlite3, json
c = sqlite3.connect('/tmp/9r.sqlite')
print('== TABEL ==')
t = [r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")]
print('  ', ', '.join(t))
print()
# cari tabel yg mencatat pemakaian
for nama in t:
    if any(k in nama.lower() for k in ('usage','log','request','metric','stat')):
        kol = [r[1] for r in c.execute(f'PRAGMA table_info({nama})')]
        n = c.execute(f'SELECT COUNT(*) FROM {nama}').fetchone()[0]
        print(f'  {nama}: {n} baris')
        print(f'     kolom: {\", \".join(kol)}')
"