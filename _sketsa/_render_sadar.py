"""Ambil HTML + data dari server untuk 3 sebab (dipakai _sadar_deploy.sh)."""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, '/app')

API = 'http://localhost:8000'
SD = Path('/tmp/sd')
SD.mkdir(parents=True, exist_ok=True)

from app.main import buat_token                       # noqa: E402
from app.models import SessionLocal, User             # noqa: E402
from app.folder import buat as buat_folder, jumlah_folder   # noqa: E402
from sqlalchemy import select                         # noqa: E402


def ambil(url, token=None):
    r = urllib.request.Request(API + url)
    if token:
        r.add_header('Cookie', 'eduai_session=' + token)
    with urllib.request.urlopen(r, timeout=40) as x:
        return json.loads(x.read().decode())


db = SessionLocal()
u = db.scalars(select(User).where(User.email == 'uji-sadar@test.local')).first()
if not u:
    u = User(email='uji-sadar@test.local', nama='Uji Sadar', password_hash='x',
             paket='penulis', kuota_mb=100, aktif=True)
    db.add(u)
    db.commit()
    db.refresh(u)

# Penuhi jatah folder (10/10) supaya sebab 'folder' masuk akal.
for i in range(jumlah_folder(db, u.id) + 1, 11):
    try:
        buat_folder(db, u, 'Folder %d' % i)
    except Exception:
        break
print('  folder: %s/10' % jumlah_folder(db, u.id))

T = buat_token(u.id)

SEBAB = {
    'folder': 'folder',
    'storage': 'storage',
    'manual': 'manual',
}

for nama, sebab in SEBAB.items():
    # halaman naskah dengan ?addon=<sebab> → SEBAB_ADDON ikut terisi
    url = '/naskah' + ('?addon=' + sebab if sebab != 'manual' else '')
    r = urllib.request.Request(API + url)
    r.add_header('Cookie', 'eduai_session=' + T)
    html = urllib.request.urlopen(r, timeout=45).read().decode('utf-8', 'replace')
    Path(SD / ('%s.html' % nama)).write_text(html, encoding='utf-8')

    # data untuk suntikan fetch
    dp = ambil('/api/paket', T)
    da = ambil('/api/addon?sebab=' + sebab, T)
    Path(SD / ('data_%s.json' % nama)).write_text(
        json.dumps({'paket': dp, 'addon': da}))

    sr = da.get('saran') or {}
    print('  %-7s sebab=%s | saran=%s | %s'
          % (nama, sr.get('sebab'), (sr.get('saran') or {}).get('nama'),
             (sr.get('diagnosis') or '')[:44]))

db.close()
