"""Uji halaman /pengaturan SEBAGAI ADMIN (pakai token sesi)."""
import sys
import urllib.request
sys.path.insert(0, '/app')

from app.auth import buat_token, SESSION_COOKIE
from app.models import SessionLocal
buat_sesi = SessionLocal

# cari user admin
with buat_sesi() as db:
    from app.models import User
    adm = db.query(User).filter(User.role == 'admin').first()
    if not adm:
        print('⛔ tidak ada user admin')
        raise SystemExit(1)
    print('admin:', adm.email, '| id', adm.id)
    tok = buat_token(adm.id)

req = urllib.request.Request('http://127.0.0.1:8000/pengaturan')
req.add_header('Cookie', f'{SESSION_COOKIE}={tok}')
t = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')
print('panjang halaman:', len(t), 'byte')
print()
print('── isi yang WAJIB ada ──')
for kata in ('Kunci Layanan', 'Simpan &amp; Uji', 'Kuota Scite',
             'Harga Token Revisi', 'Scopus', 'OpenAlex', 'Scite'):
    print('  %-22s %s' % (kata, '✅ ADA' if kata in t else '❌ tidak'))
print()
print('── kunci utuh TIDAK boleh tampil ──')
import re
utuh = re.findall(r'[A-Za-z0-9_\-]{40,}', t)
print('  string panjang (>=40) di halaman:', len(utuh), '(harus 0 atau hanya token sesi)')
for s in utuh[:3]:
    print('    contoh:', s[:30], '...')
