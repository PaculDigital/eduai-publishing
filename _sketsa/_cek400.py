"""Cek cepat: kok unggah balas 400? Pesan aslinya apa?"""
import sys
import urllib.error
import urllib.request

sys.path.insert(0, '/app')

from app.main import buat_token                     # noqa: E402
from app.models import SessionLocal, User           # noqa: E402

db = SessionLocal()
u = User(email='uji-cek400@test.local', nama='Cek400', password_hash='x',
         paket='penulis', kuota_mb=100, aktif=True)
db.add(u)
db.commit()
db.refresh(u)
T = buat_token(u.id)

batas = '----cek400'
isi = b'x' * (1024 * 1024)
kepala = (
    '--' + batas + '\r\n'
    'Content-Disposition: form-data; name="berkas"; filename="a.pdf"\r\n'
    'Content-Type: application/pdf\r\n\r\n'
).encode()
ekor = ('\r\n--' + batas + '--\r\n').encode()
body = kepala + isi + ekor

r = urllib.request.Request('http://localhost:8000/unggah', data=body, method='POST')
r.add_header('Cookie', 'eduai_session=' + T)
r.add_header('Content-Type', 'multipart/form-data; boundary=' + batas)
try:
    x = urllib.request.urlopen(r, timeout=60)
    print('  HTTP', x.status, x.read()[:400])
except urllib.error.HTTPError as e:
    print('  HTTP', e.code, '->', e.read()[:400])

db.delete(u)
db.commit()
db.close()
