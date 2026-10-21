"""Pulihkan jatah uji Asih + buktikan TOMBOL muncul saat jatah ADA.

⚠️ Hanya menyentuh JATAH/PEMAKAIAN milik uji (user asih.susanti@eduai.test),
   BUKAN data produksi. Kembalikan `dipakai` ke 0 supaya tombol tampil.
"""
import http.client
import re
import sys

sys.path.insert(0, '/app')
from app import auth as A                                          # noqa: E402
from app import kuota as Q                                         # noqa: E402
from app.models import (User, FileBerkas, SessionLocal,            # noqa: E402
                        KonversiNaskah)

db = SessionLocal()
f = db.get(FileBerkas, 81)
u = db.get(User, f.user_id)
print(f'naskah fid=81 milik: {u.email} (id={u.id})')

#  ── Bersihkan pemakaian konversi milik user uji ini (berkas fid=81) ──
n = 0
for b in db.query(KonversiNaskah).filter(KonversiNaskah.user_id == u.id).all():
    print(f'  hapus pemakaian: id={b.id} fid={getattr(b, "file_id", "?")} '
          f'token={getattr(b, "token_dipotong", "?")}')
    db.delete(b)
    n += 1
db.commit()
print(f'  → {n} baris pemakaian dihapus')

j = Q.jatah_konversi(db, u)
print(f'jatah sekarang: {j}')
print()

#  ── Ambil halaman lagi, cari tombol ──
tok = A.buat_token(u.id)
k = http.client.HTTPConnection('127.0.0.1', 8000, timeout=180)
k.request('GET', '/artikel/81/konversi',
          headers={'Cookie': f'{A.SESSION_COOKIE}={tok}'})
r = k.getresponse()
html = r.read().decode()
print(f'HTTP {r.status} · {len(html):,} kar')
print()
print('=== TOMBOL MUNCUL? ===')
if 'Mulai Konversi' in html:
    i = html.find('Mulai Konversi')
    print('  ✅ "Mulai Konversi" ADA')
    print('   ', html[max(0, i-260):i+60].replace('\n', ' ')[-320:])
else:
    print('  ❌ masih tidak ada')
m = re.search(r'<form[^>]*action="([^"]*)"', html)
print('  form action :', m.group(1) if m else 'TIDAK ADA')
mm = re.search(r'(\d+)× konversi', html)
print('  jatah tampil:', mm.group(0) if mm else '—')
print('  "Jatah habis":', 'ADA' if 'Jatah habis' in html else 'tidak ada')
db.close()
