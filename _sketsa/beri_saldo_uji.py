"""Beri saldo uji 2 Token Revisi utk user 3 (uji anti-524 27Sep)."""
import datetime
from sqlalchemy import text
from app.models import SessionLocal

db = SessionLocal()
db.execute(text(
    "INSERT INTO saldo_token (user_id, jumlah, sisa, sumber, catatan, "
    "order_id, dibuat) VALUES (3, 2, 2, 'uji', "
    "'uji anti-524 27Sep', '', :d)"),
    {"d": str(datetime.datetime.utcnow())})
db.commit()
print('saldo uji +2 diberikan')
