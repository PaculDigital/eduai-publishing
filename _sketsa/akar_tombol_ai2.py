"""Panggil RUTE /tinjau/{token} langsung lewat TestClient — lihat apa yang dicetak.

Ini bukan menebak: menjalankan rute ASLI dengan data ASLI, lalu mencari
"Periksa dengan AI" di HTML hasilnya + mencetak kenapa kalau tidak ada.
"""
import sys

sys.path.insert(0, '/app')

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.models import SessionLocal, Pembimbingan  # noqa: E402

TOKEN = 'GDvcGFpt212WDANwJcaym_YkRx2byUl4cu-EJCwQkus'

db = SessionLocal()
b = db.query(Pembimbingan).filter(Pembimbingan.id == 1).one()
DB_TOKEN = b.token_sidik
db.close()

with TestClient(app) as c:
    r = c.get(f'/tinjau/{TOKEN}', follow_redirects=False)
    print('HTTP       :', r.status_code)
    print('ukuran     :', len(r.text), 'byte')
    loc = r.headers.get('location')
    if loc:
        print('REDIRECT ke:', loc)
    print()
    for tanda in ('Periksa dengan AI', 'Buka di editor', 'alat-baca',
                  'Belum ada naskah', 'ai_aktif'):
        print(f'  {"ADA " if tanda in r.text else "TIDAK"} — {tanda!r}')
    print()
    #  Kalau halaman ini bukan editor, cetak judulnya
    import re
    t = re.search(r'<title>(.*?)</title>', r.text, re.S)
    print('JUDUL HALAMAN:', t.group(1).strip() if t else '(tidak ada)')
    #  Cari nama template yang disebut (kalau ada komentar)
    print()
    print('--- 400 karakter pertama ---')
    print(r.text[:400])

print()
print('DB token_sidik:', DB_TOKEN[:20] + '…')
