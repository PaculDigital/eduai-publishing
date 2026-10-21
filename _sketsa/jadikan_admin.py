"""Jadikan akun admin + set password baru (untuk akses halaman setelan harga).

Dijalankan SEKALI. Password ADMIN diambil dari argumen supaya tidak tertulis
di berkas ini.
"""
import secrets
import sys
import os

sys.path.insert(0, '/app')
from app.auth import hash_password
from app.models import SessionLocal, User

pw = sys.argv[1] if len(sys.argv) > 1 else None
if not pw:
    pw = secrets.token_urlsafe(9)
    dibuat = True
else:
    dibuat = False

db = SessionLocal()
try:
    u = db.query(User).filter(User.email == 'wulan@bikinaja.me').first()
    if not u:
        print('❌ user tidak ditemukan')
        sys.exit(1)
    lama = u.role
    u.role = 'admin'
    u.password_hash = hash_password(pw)
    db.commit()
    print(f'✅ {u.email} (id {u.id})')
    print(f'   role: {lama} → {u.role}')
    print(f'   password: {pw}')
finally:
    db.close()
