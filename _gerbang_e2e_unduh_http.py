"""UJI E2E — Rute /unduh & /folder-pilihan lewat HTTP NYATA (TestClient).

Dijalankan DI DALAM container. Memakai DB SALINAN (jangan sentuh produksi).
Bukti: respons JSON yang SUNGGUHAN, bukan pembacaan kode.
"""
from __future__ import annotations

import os
import secrets
import shutil
import sys
import tempfile

TMP = tempfile.mkdtemp(prefix='uji_e2e_unduh_')
DB = os.path.join(TMP, 'uji.db')
shutil.copyfile('/app/data/eduai.db', DB)
os.environ['EDUAI_DB'] = DB
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app import models as M  # noqa: E402

eng = create_engine(f'sqlite:///{DB}', connect_args={'check_same_thread': False})
M.engine = eng
M.SessionLocal = sessionmaker(bind=eng, expire_on_commit=False)

from app import main as appmod  # noqa: E402

L = G = 0


def cek(n, s, k=''):
    global L, G
    if s:
        L += 1
        print(f'  LULUS  {n} {k}')
    else:
        G += 1
        print(f'  GAGAL  {n} {k}')


db = M.SessionLocal()
u = db.query(M.User).first()
#  Naskah milik user + profil
fb = (db.query(M.FileBerkas)
        .filter(M.FileBerkas.user_id == u.id,
                M.FileBerkas.nama_simpan.notlike('%.pdf')).first())
if fb is None:
    fb = M.FileBerkas(user_id=u.id, nama='Naskah Uji.docx',
                      nama_simpan=f'{secrets.token_hex(8)}.docx',
                      ukuran=1000, tipe='application/vnd.openxmlformats')
    db.add(fb)
    db.commit()
    db.refresh(fb)
fk = M.Folder(user_id=u.id, nama=f'WS-E2E-{secrets.token_hex(2)}', warna='hijau')
db.add(fk)
db.commit()
db.refresh(fk)
uid_u, fid_u, folder_u = u.id, fb.id, fk.id
db.close()

#  ── Token sesi untuk user (pola auth yang SUDAH ADA) ─────────────────────
from app import auth as A  # noqa: E402
db = M.SessionLocal()
u2 = db.get(M.User, uid_u)
tok = A.buat_token(uid_u)
db.close()
if not tok:
    print('  ❌ tidak bisa buat token — berhenti'); sys.exit(2)

kl = TestClient(appmod.app, cookies={A.SESSION_COOKIE: tok})

#  ══ E2E-1: /folder-pilihan balas daftar folder nyata ════════════════════
r = kl.get('/api/ai/v1/jurnal/folder-pilihan')
jk = r.json() if r.status_code == 200 else {}
cek('E1a /folder-pilihan → 200', r.status_code == 200, f'({r.status_code})')
cek('E1b balas ok + daftar folder', jk.get('ok') is True and isinstance(jk.get('folder'), list),
    f'({len(jk.get("folder", []))} folder)')
cek('E1c folder uji ADA di daftar',
    any(f['id'] == folder_u for f in jk.get('folder', [])))

#  ══ E2E-2: /unduh TANPA login → ditolak ═════════════════════════════════
kosong = TestClient(appmod.app)
r2 = kosong.post('/api/ai/v1/jurnal/unduh?file_id=%d&kunci=x' % fid_u)
cek('E2a /unduh tanpa login → 401/303 (ditolak)',
    r2.status_code in (401, 303, 403), f'({r2.status_code})')

#  ══ E2E-3: /unduh artikel TIDAK ADA → 404 jujur ═════════════════════════
r3 = kl.post(f'/api/ai/v1/jurnal/unduh?file_id={fid_u}&bab=BAB%20II&kunci=tidak-ada')
cek('E3a /unduh kunci palsu → 404 + pesan jelas',
    r3.status_code == 404, f'({r3.status_code})')

#  ══ E2E-4: /unduh file_id milik orang lain → 404 (pagar) ════════════════
r4 = kl.post('/api/ai/v1/jurnal/unduh?file_id=999999&kunci=x')
cek('E4a naskah tak dikenal → 404 (pagar kepemilikan)',
    r4.status_code == 404, f'({r4.status_code})')

print(f'\nTOTAL: {L} LULUS / {G} GAGAL')
sys.exit(1 if G else 0)
