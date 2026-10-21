#!/usr/bin/env python3
"""BANDING: kolom MODEL vs kolom DB → tambahkan yang KURANG (26Sep26).

AKAR: Wulan menambah kolom di MODEL saja, lupa daftarkan di
`_migrasi_kolom()` → INSERT gagal ("no column named …") → peta
TIDAK tersimpan (GAGAL SENYAP di log, user tidak tahu).

CARA AMAN: baca kolom model dari SQLAlchemy (sumber kebenaran),
bandingkan dengan PRAGMA table_info DB, lalu ALTER TABLE untuk
SETIAP kolom yang kurang. Idempoten.
"""
import os
import sqlite3
import sys

sys.path.insert(0, '/app')
os.environ.setdefault('EDUAI_DATA_DIR', '/app/data')

from app import models                                                # noqa: E402

DB = '/app/data/eduai.db'
TABEL_PENTING = ('users', 'profil_dokumen')

kon = sqlite3.connect(DB)
for tabel in TABEL_PENTING:
    kls = None
    for nama in dir(models):
        o = getattr(models, nama)
        if isinstance(o, type) and hasattr(o, '__tablename__'):
            if o.__tablename__ == tabel:
                kls = o
                break
    if kls is None:
        print(f'⚠️  model {tabel} tidak ketemu')
        continue

    kol_db = {r[1] for r in kon.execute(f'PRAGMA table_info({tabel})')}
    kol_model = {c.name: c.type for c in kls.__table__.columns}
    kurang = [k for k in kol_model if k not in kol_db]
    print(f'\n── {tabel}: model {len(kol_model)} · db {len(kol_db)} '
          f'· KURANG {len(kurang)} ──')
    for k in kurang:
        tipe = kol_model[k]
        # petakan tipe SQLAlchemy → SQLite (longgar tapi aman)
        t = str(tipe).upper()
        if 'INT' in t:
            sql_tipe = 'INTEGER'
        elif 'DATETIME' in t or 'DATE' in t:
            sql_tipe = 'DATETIME'
        elif 'TEXT' in t:
            sql_tipe = 'TEXT'
        elif 'BOOL' in t:
            sql_tipe = 'INTEGER'
        else:
            sql_tipe = 'VARCHAR(200)'
        # kolom NOT NULL perlu DEFAULT supaya baris lama valid
        cek_notnull = kls.__table__.columns[k].nullable is False
        tambah = f' DEFAULT \'\'' if (cek_notnull and 'VARCHAR' in sql_tipe) else ''
        if cek_notnull and sql_tipe == 'INTEGER':
            tambah = ' DEFAULT 0'
        try:
            kon.execute(f'ALTER TABLE {tabel} ADD COLUMN {k} {sql_tipe}{tambah}')
            print(f'   ✅ + {k} {sql_tipe}{tambah}')
        except Exception as e:
            print(f'   ⚠️  {k}: {e}')
kon.commit()

print('\n── verifikasi akhir ──')
for tabel in TABEL_PENTING:
    kol_db = {r[1] for r in kon.execute(f'PRAGMA table_info({tabel})')}
    kls = next((getattr(models, n) for n in dir(models)
                if isinstance(getattr(models, n), type)
                and getattr(getattr(models, n), '__tablename__', '') == tabel), None)
    if kls:
        kol_model = {c.name for c in kls.__table__.columns}
        sisa = kol_model - kol_db
        print(f'  {tabel}: {len(kol_db)} kolom · sisa kurang: {sorted(sisa) or "TIDAK ADA ✅"}')
kon.close()
