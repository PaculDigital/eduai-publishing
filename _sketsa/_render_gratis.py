"""Render halaman GRATIS — bukti panel "ajak upgrade" (ACC Bos 15Sep26).

KENAPA: user paket Gratis TIDAK boleh beli AddOn. Versi lama menampilkan
popup dengan 5 tombol mati (bikin bingung). Versi baru: panel ajakan
upgrade dengan pesan JELAS + tombol ke daftar paket.

Diuji 2 pemicu:
  A. gerbang FOLDER (user gratis penuh jatah folder → panel muncul)
  B. gerbang STORAGE (unggah ditolak → panel muncul)
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, '/app')

API = 'http://localhost:8000'
SD = Path('/tmp/sd')
SD.mkdir(parents=True, exist_ok=True)

from app.main import buat_token                        # noqa: E402
from app.models import SessionLocal, User              # noqa: E402
from app.folder import buat as buat_folder, jumlah_folder   # noqa: E402
from sqlalchemy import select                          # noqa: E402


def ambil(url, token=None):
    r = urllib.request.Request(API + url)
    if token:
        r.add_header('Cookie', 'eduai_session=' + token)
    with urllib.request.urlopen(r, timeout=40) as x:
        return json.loads(x.read().decode())


db = SessionLocal()
u = db.scalars(select(User).where(User.email == 'uji-gratis-render@test.local')).first()
if not u:
    u = User(email='uji-gratis-render@test.local', nama='Uji Gratis',
             password_hash='x', paket='gratis', kuota_mb=30, aktif=True)
    db.add(u)
    db.commit()
    db.refresh(u)

# Penuhi jatah folder gratis (3) supaya gerbang folder terpicu
for i in range(jumlah_folder(db, u.id) + 1, 4):
    try:
        buat_folder(db, u, 'Folder %d' % i)
    except Exception as e:
        print('  (stop: %s)' % e)
        break
print('  gratis: folder %s/3 | boleh_addon=%s'
      % (jumlah_folder(db, u.id), u.paket != 'gratis'))
print('  ID user gratis = %s' % u.id)

T = buat_token(u.id)

# ── A. gerbang folder (?addon=folder → JS panggil bukaTopup) ─────────────
for nama, url in (('gratis_folder', '/naskah?addon=folder'),
                  ('gratis_biasa', '/naskah')):
    r = urllib.request.Request(API + url)
    r.add_header('Cookie', 'eduai_session=' + T)
    html = urllib.request.urlopen(r, timeout=45).read().decode('utf-8', 'replace')
    Path(SD / ('%s.html' % nama)).write_text(html, encoding='utf-8')
    blok = html.count('ajak-upgrade')
    print('  %-14s %s byte | panel ajak-upgrade=%d | BOLEH_ADDON=%s'
          % (nama, len(html), blok,
             'false' if 'window.BOLEH_ADDON = false' in html else 'true'))

dp = ambil('/api/paket', T)
da = ambil('/api/addon?sebab=folder', T)
Path(SD / 'data_gratis.json').write_text(json.dumps({'paket': dp, 'addon': da}))
print('  boleh_beli dari server = %s | saran = %s'
      % (da.get('boleh_beli'), (da.get('saran') or {}).get('saran')))

db.close()
