"""Render popup Tambah Kuota dengan DATA NYATA dari server.

MASALAH: render dari file:// membuat fetch('/api/paket') GAGAL, jadi popup
cuma menampilkan "Tidak bisa memuat daftar paket" — bukan tampilan asli.

SOLUSI (dipakai skrip ini): suntikkan hasil /api/paket dan /api/addon
SUNGGUHAN (diambil dari server) ke dalam HTML sebagai data mock, sehingga
JS halaman menggambar kartu seperti di produksi. Tampilan yang dirender
sama persis dengan yang dilihat user.
"""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, '/app')

API = 'http://localhost:8000'
CHROME = '/opt/data/chrome/chrome'
KELUAR = Path('/tmp/pp')
KELUAR.mkdir(parents=True, exist_ok=True)

from app.main import buat_token                      # noqa: E402
from app.models import SessionLocal, User            # noqa: E402
from sqlalchemy import select                        # noqa: E402


def ambil(url, token=None):
    r = urllib.request.Request(API + url)
    if token:
        r.add_header('Cookie', 'eduai_session=' + token)
    with urllib.request.urlopen(r, timeout=30) as x:
        return json.loads(x.read().decode())


db = SessionLocal()
RENCANA = [
    ('penulis', 'uji-render-addon@test.local', 'Penulis (berbayar)'),
    ('gratis', 'uji-render-addon-gratis@test.local', 'Gratis (terkunci)'),
]

for nama, email, label in RENCANA:
    u = db.scalars(select(User).where(User.email == email)).first()
    if not u:
        print('  ✗ %s tidak ada — dilewati' % email)
        continue
    T = buat_token(u.id)

    # ── data SUNGGUHAN dari server (bukan karangan) ─────────────────────
    d_paket = ambil('/api/paket', T)
    d_addon = ambil('/api/addon', T)
    print('  %-8s paket=%d addon=%d boleh_beli=%s'
          % (nama, len(d_paket.get('paket', [])), len(d_addon.get('addon', [])),
             d_addon.get('boleh_beli')))

    # ── halaman naskah SUNGGUHAN ───────────────────────────────────────
    r = urllib.request.Request(API + '/naskah')
    r.add_header('Cookie', 'eduai_session=' + T)
    html = urllib.request.urlopen(r, timeout=45).read().decode('utf-8', 'replace')

    # ── suntikkan: (a) data mock, (b) auto-buka popup ───────────────────
    suntik = """
<script>
/* RENDER UJI: fetch diblokir di file://, jadi data SUNGGUHAN dari server
   disuntikkan di sini. Tampilan yang digambar = sama dengan produksi. */
(function () {
  var _fetch = window.fetch;
  var PAKET = %s;
  var ADDON = %s;
  window.fetch = function (url, opt) {
    var u = String(url);
    if (u.indexOf('/api/paket') === 0) {
      return Promise.resolve({ ok: true, json: function () {
        return Promise.resolve(PAKET); } });
    }
    if (u.indexOf('/api/addon') === 0) {
      return Promise.resolve({ ok: true, json: function () {
        return Promise.resolve(ADDON); } });
    }
    return _fetch.apply(this, arguments);
  };
  window.addEventListener('load', function () {
    setTimeout(function () { window.bukaTopup && window.bukaTopup(); }, 200);
  });
})();
</script>
""" % (json.dumps(d_paket), json.dumps(d_addon))

    html = html.replace('</body>', suntik + '</body>', 1)
    p_html = KELUAR / ('auto_%s.html' % nama)
    p_html.write_text(html, encoding='utf-8')
    print('     html %s byte' % len(html))

db.close()

# ── render: popup saja (crop tengah) + versi HP ──────────────────────────
for nama, _, _ in RENCANA:
    p_html = KELUAR / ('auto_%s.html' % nama)
    if not p_html.exists():
        continue
    for tag, w, h in (('', 900, 1150), ('_hp', 420, 1150)):
        png = KELUAR / ('popup_%s%s.png' % (nama, tag))
        subprocess.run(
            [CHROME, '--headless=new', '--no-sandbox', '--disable-gpu',
             '--hide-scrollbars', '--window-size=%d,%d' % (w, h),
             '--screenshot=' + str(png), '--virtual-time-budget=4000',
             'file://' + str(p_html)], capture_output=True, timeout=115)
        print('  %s -> %s byte' % (png.name, png.stat().st_size if png.exists() else 'GAGAL'))
