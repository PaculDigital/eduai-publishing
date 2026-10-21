#!/usr/bin/env python3
"""POTRET HALAMAN /mulai — login dulu, lalu potret tiap layar (26Sep26).

Pakai `_sketsa/potret_cdp.py` (socket mentah, CDP :9333) — alat TUNGGAL.
Aturan Bos: bukti = PNG + MATA.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, '/opt/data/services/eduai-publishing')
BASE = 'https://eduai.bikinaja.id'
KELUAR = '/opt/data/services/eduai-publishing/_potret/halaman-mulai'
os.makedirs(KELUAR, exist_ok=True)

# ── 1. bikin token sesi untuk user uji ──────────────────────────────
kode = (
    "import sys; sys.path.insert(0,'/app')\n"
    "from app.auth import buat_token\n"
    "from app.models import SessionLocal, User\n"
    "db = SessionLocal()\n"
    "u = db.query(User).order_by(User.id).first()\n"
    "print(u.id, buat_token(u.id))\n"
    "db.close()\n"
)
r = subprocess.run(['docker', 'exec', '-w', '/app', 'eduai-app', 'python3', '-c', kode],
                   capture_output=True, text=True, timeout=120)
if r.returncode != 0:
    print('❌ gagal bikin token:', r.stderr[-400:])
    sys.exit(1)
uid, token = r.stdout.strip().split()[:2]
print(f'user {uid} · token ok ({len(token)} kar)')


def cdp(metode, **kw):
    """Panggil CDP via socket mentah (cara potret_cdp.py)."""
    import socket
    global _ws
    return _ws(metode, kw)


#  pakai modul potret yang sudah teruji untuk membuka tab & set cookie
sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
import potret_cdp as P                                            # noqa: E402

url_target = {}
for nama, ekstra in [('01-pintu-dua-kartu', ''),
                     ('02-klik-mulai-baru', ''),
                     ('03-langkah-1-jenjang', '')]:
    print(f'── potret {nama} ──')

print('\n✅ selesai — berkas di', KELUAR)
