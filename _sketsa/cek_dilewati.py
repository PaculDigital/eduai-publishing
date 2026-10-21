"""Verifikasi DB status dilewati catatan 11 (dijalankan di container)."""
from sqlalchemy import text
from app.models import SessionLocal

db = SessionLocal()
cols = [c[1] for c in db.execute(
    text("PRAGMA table_info(catatan_pembimbing)")).fetchall()]
print('kolom lew:', [c for c in cols if 'lew' in c])
print(db.execute(text(
    "SELECT id, dilewati, keadaan FROM catatan_pembimbing "
    "WHERE id IN (10,11)")).fetchall())
