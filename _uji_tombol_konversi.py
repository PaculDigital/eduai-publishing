"""Buktikan TOMBOL 'Mulai Konversi' benar-benar MUNCUL di halaman.

Bukan tebak-tebakan: ambil HTML sungguhan lewat HTTP, cari tombolnya.
"""
import http.client
import re
import sys

sys.path.insert(0, '/app')
from app import auth as A                                          # noqa: E402
from app.models import User, FileBerkas, SessionLocal              # noqa: E402

db = SessionLocal()
f = db.get(FileBerkas, 81)
u = db.get(User, f.user_id)
tok = A.buat_token(u.id)

k = http.client.HTTPConnection('127.0.0.1', 8000, timeout=180)
k.request('GET', '/artikel/81/konversi',
          headers={'Cookie': f'{A.SESSION_COOKIE}={tok}'})
r = k.getresponse()
html = r.read().decode()
print(f'HTTP {r.status} · {len(html):,} kar')
print()

print('=== BUKTI 1: tombol "Mulai Konversi" ADA di HTML? ===')
if 'Mulai Konversi' in html:
    i = html.find('Mulai Konversi')
    print('  ✅ ADA — konteks:')
    print('   ', html[max(0, i-300):i+80].replace('\n', ' ')[-360:])
else:
    print('  ❌ TIDAK ADA')

print()
print('=== BUKTI 2: form POST ke rute konversi? ===')
m = re.search(r'<form[^>]*action="([^"]*)"', html)
print('  form action:', m.group(1) if m else 'TIDAK ADA')

print()
print('=== BUKTI 3: jatah terlihat user? ===')
for pola in (r'(\d+)× konversi', r'Jatah habis', r'Sisa jatah'):
    mm = re.search(pola, html)
    print(f'  {pola:20} →', mm.group(0) if mm else '—')

print()
print('=== BUKTI 4: pesan mutu Jev ikut? ===')
print('  "Pemeriksaan Mutu"', '✅' if 'Pemeriksaan Mutu' in html else '❌')
print('  "Kesiapan:"', '✅' if 'Kesiapan:' in html else '❌')
db.close()
