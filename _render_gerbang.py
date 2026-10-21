#!/usr/bin/env python3
"""Render BUKTI DUA GERBANG (untuk vision + screenshot ke Bos).

Skenario yang dirender:
  A. Peringatan "jatah folder penuh" + TOMBOL ADDON (user penulis)
  B. Popup Tambah Kuota terbuka otomatis (pemicu ?addon=storage)

Data diambil dari server sungguhan; fetch disuntikkan karena render
memakai file:// (lihat _popup_1_ambil.sh untuk pola yang sama).
"""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, '/app')

API = 'http://localhost:8000'
CHROME = '/opt/data/chrome/chrome'
PP = Path('/tmp/gg')
PP.mkdir(parents=True, exist_ok=True)

from app.main import buat_token                      # noqa: E402
from app.models import SessionLocal, User            # noqa: E402
from app.folder import buat as buat_folder           # noqa: E402
from sqlalchemy import select                        # noqa: E402


def ambil(url, token=None):
    r = urllib.request.Request(API + url)
    if token:
        r.add_header('Cookie', 'eduai_session=' + token)
    with urllib.request.urlopen(r, timeout=40) as x:
        return json.loads(x.read().decode())


db = SessionLocal()

# ── user penulis khusus render, jatah folder DIPENUHI 10/10 ──────────────
u = db.scalars(select(User).where(User.email == 'uji-gg@test.local')).first()
if not u:
    u = User(email='uji-gg@test.local', nama='Uji GG', password_hash='x',
             paket='penulis', kuota_mb=100, aktif=True)
    db.add(u)
    db.commit()
    db.refresh(u)
from app.folder import jumlah_folder                # noqa: E402
sudah = jumlah_folder(db, u.id)
for i in range(sudah + 1, 11):
    try:
        buat_folder(db, u, 'Folder %d' % i)
    except Exception as e:
        print('  (folder stop: %s)' % e)
        break
print('  folder sekarang: %s/10' % jumlah_folder(db, u.id))

T = buat_token(u.id)
d_paket = ambil('/api/paket', T)
d_addon = ambil('/api/addon', T)

SKRIP = """
<script>
(function () {
  var DATA = __DATA__;
  var _f = window.fetch;
  window.fetch = function (url) {
    var s = String(url);
    if (s.indexOf('/api/paket') === 0)
      return Promise.resolve({ok:true, json:function(){return Promise.resolve(DATA.paket);}});
    if (s.indexOf('/api/addon') === 0)
      return Promise.resolve({ok:true, json:function(){return Promise.resolve(DATA.addon);}});
    return _f.apply(this, arguments);
  };
  window.addEventListener('load', function () {
    setTimeout(function () {
      var tb = document.querySelector('button[onclick*="bukaTopup"]');
      if (tb) tb.click();
    }, 500);
  });
})();
</script>
"""

DATA = json.dumps({'paket': d_paket, 'addon': d_addon})

# ── A: halaman /naskah dengan ?addon=storage (pemicu gerbang folder) ─────
for nama, url, sufix in (
    ('jatah_penuh', '/naskah?addon=storage', 'A'),
):
    r = urllib.request.Request(API + url)
    r.add_header('Cookie', 'eduai_session=' + T)
    html = urllib.request.urlopen(r, timeout=45).read().decode('utf-8', 'replace')
    html = html.replace('</body>', SKRIP.replace('__DATA__', DATA) + '</body>', 1)
    p = PP / ('%s.html' % nama)
    p.write_text(html, encoding='utf-8')
    print('  %s: %s byte | tombol addon=%d | pemicu url=%s'
          % (nama, len(html), html.count('fd-tombol-addon'),
             'addon=storage' in html or 'pemicuDariURL' in html))
    png = PP / ('%s.png' % nama)
    subprocess.run([CHROME, '--headless=new', '--no-sandbox', '--disable-gpu',
                    '--hide-scrollbars', '--window-size=900,1300',
                    '--screenshot=' + str(png),
                    '--virtual-time-budget=12000',
                    '--run-all-compositor-stages-before-draw',
                    'file://' + str(p)], capture_output=True, timeout=150)
    print('     png -> %s byte' % (png.stat().st_size if png.exists() else 'GAGAL'))

db.close()
