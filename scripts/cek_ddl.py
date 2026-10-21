"""Cek DDL tabel pembimbingan_berkas + catatan_pembimbing (HANYA BACA)."""
from sqlalchemy import text
from app.models import SessionLocal

db = SessionLocal()
rows = db.execute(text(
    "SELECT name, sql FROM sqlite_master WHERE type='table' AND "
    "name IN ('pembimbingan_berkas', 'catatan_pembimbing', 'files') "
)).fetchall()
for nama, ddl in rows:
    print('==', nama, '==')
    print(ddl)
    print()
