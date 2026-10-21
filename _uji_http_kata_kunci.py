"""UJI E2E HTTP — tombol "EduAi bantu isi" & pesan 0-hasil (13 Okt 2026).

Dijalankan DI DALAM container. DB SALINAN (jangan sentuh produksi).
Yang dibuktikan: RESPONS JSON SUNGGUHAN lewat rute nyata, bukan baca kode.

Rute yang diuji:
  POST /api/ai/v1/jurnal/kata-kunci-ai   (tombol "EduAi bantu isi")
  POST /api/ai/v1/jurnal/cari-ai         (pesan 0-hasil jujur)

Cara jalan:
  docker cp _uji_http_kata_kunci.py eduai-app:/app/_uji_http_kk.py
  docker exec eduai-app python3 /app/_uji_http_kk.py
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

TMP = tempfile.mkdtemp(prefix='uji_kk_')
DB = os.path.join(TMP, 'uji.db')
shutil.copyfile('/app/data/eduai.db', DB)
os.environ['EDUAI_DB'] = DB
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')

from fastapi.testclient import TestClient                          # noqa: E402
from sqlalchemy import create_engine                              # noqa: E402
from sqlalchemy.orm import sessionmaker                           # noqa: E402

from app import models as M                                       # noqa: E402

eng = create_engine(f'sqlite:///{DB}', connect_args={'check_same_thread': False})
M.engine = eng
M.SessionLocal = sessionmaker(bind=eng, expire_on_commit=False)

from app import main as appmod                                    # noqa: E402

L = G = 0
GAGAL: list[str] = []


def cek(nama, syarat, ket=''):
    global L, G
    if syarat:
        L += 1
        print(f'  LULUS  {nama} {ket}')
    else:
        G += 1
        GAGAL.append(nama)
        print(f'  GAGAL  {nama} <-- {ket}')


print('═══ UJI HTTP TOMBOL "EduAi bantu isi" ═══')
klien = TestClient(appmod.app)

#  ── cari user + berkas yang ADA di DB salinan ──
db = M.SessionLocal()
try:
    u = db.query(M.User).first()
    b = (db.query(M.FileBerkas)
         .filter(M.FileBerkas.terhapus_pada.is_(None)).first())
    uid, fid = u.id, (b.id if b else 0)
    print(f'  (user={uid} · berkas={fid})')
finally:
    db.close()

#  Login: pakai cara RESMI proyek — `dependency_overrides[wajib_login_api]`
#  (dipakai juga oleh _gerbang_halaman_referensi.py :96 & _gerbang_rute_jurnal.py :88).
from app import rute_jurnal as RJ                                 # noqa: E402

db = M.SessionLocal()
try:
    u = db.query(M.User).first()
    b = (db.query(M.FileBerkas)
         .filter(M.FileBerkas.terhapus_pada.is_(None)).first())
    uid, fid = u.id, (b.id if b else 0)
    print(f'  (user={uid} · berkas={fid})')
finally:
    db.close()

appmod.app.dependency_overrides[RJ.wajib_login_api] = lambda: u
login_ok = True

#  ── ① TOMBOL: tanpa file_id & tanpa judul → pesan jelas ──
r = klien.post('/api/ai/v1/jurnal/kata-kunci-ai')
j = r.json() if r.headers.get('content-type', '').startswith('application/json') else {}
cek('① tanpa naskah → jawab jujur (bukan error 500)',
    r.status_code == 200, f'HTTP {r.status_code}')
cek('①a ada pesan jelas (bukan ok)', j.get('ok') is False, str(j)[:70])
cek('①b minta tulis judul / pilih naskah',
    'judul' in str(j.get('pesan', '')).lower()
    or 'naskah' in str(j.get('pesan', '')).lower(),
    str(j.get('pesan'))[:70])

#  ── ② TOMBOL: judul yang DIKENAL KAMUS → sumber 'kamus' (Rp 0) ──
if login_ok:
    r2 = klien.post('/api/ai/v1/jurnal/kata-kunci-ai',
                    params={'judul': 'pengaruh kualitas produk terhadap '
                                     'keputusan pembelian'})
    j2 = r2.json()
    cek('② judul dikenal kamus → ok', j2.get('ok') is True, str(j2)[:80])
    if j2.get('ok'):
        cek('②a sumber = kamus (tanpa panggil AI)',
            j2.get('sumber_kata_kunci') == 'kamus',
            f"sumber={j2.get('sumber_kata_kunci')}")
        cek('②b ada usul kata kunci siap-pakai',
            bool((j2.get('usul') or '').strip()), f"usul={j2.get('usul')}")
        cek('②c konsep bisa diubah user (ada daftar)',
            len(j2.get('konsep') or []) > 0,
            f"konsep={len(j2.get('konsep') or [])}")

    #  ── ③ CARI-AI: kata kunci ngawur TOTAL → pesan 0-hasil yang jelas ──
    if fid:
        r3 = klien.post('/api/ai/v1/jurnal/cari-ai',
                        params={'file_id': fid, 'bab': 'BAB II',
                                'kata_kunci': 'zzqqxx tidak ada apa pun'})
        j3 = r3.json()
        cek('③ kata kunci ngawur → ok=False (jujur)', j3.get('ok') is False,
            str(j3)[:80])
        cek('③a kode jujur terisi',
            j3.get('kode') in ('tidak_ada_hasil', 'tidak_dipetakan'),
            f"kode={j3.get('kode')}")
        cek('③b pesan menyebut cara memperbaiki (ubah/Indonesia)',
            ('ubah' in str(j3.get('pesan', '')).lower()
             or 'Garuda' in str(j3.get('pesan', ''))
             or 'memetakan' in str(j3.get('pesan', '')).lower()),
            str(j3.get('pesan'))[:70])
        cek('③c pesan TIDAK pakai kata ragu ("sepertinya")',
            'sepertinya' not in str(j3.get('pesan', '')).lower())

print()
if GAGAL:
    print('  Gagal:', ', '.join(GAGAL))
print(f'═══ {L} LULUS / {G} GAGAL ═══')
sys.exit(1 if G else 0)
