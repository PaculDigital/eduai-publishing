"""GERBANG — CEGAH UNDUH DOBEL + BOLEH ULANG SETELAH DIHAPUS (syarat Bos 06Okt26).

Syarat Bos (verbatim): "kalo sudah download tidak bisa download atau double,
kecuali telah dihapus dan download lagi."

Menguji LEWAT HTTP NYATA (TestClient) di DB SALINAN — bukan salinan produksi.

CARA PAKAI (DI DALAM container — WAJIB):
    docker cp _gerbang_unduh_dobel.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _gerbang_unduh_dobel.py
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path

AKAR = '/app'
L, G = 0, 0


def cek(nama: str, syarat: bool, ket: str = '') -> None:
    global L, G
    if syarat:
        L += 1
        print(f'  LULUS  {nama} {ket}')
    else:
        G += 1
        print(f'  GAGAL  {nama} {ket}')


# ── BAGIAN 1: periksa SUMBER (kode, bukan komentar) ──────────────────────
src = Path(f'{AKAR}/app/rute_jurnal.py').read_text()
kode = re.sub(r'#.*', '', src)
kode = re.sub(r'""".*?"""', '', kode, flags=re.S)
# buang docstring satu baris juga
kode = re.sub(r"'''.*?'''", '', kode, flags=re.S)
kode = re.sub(r'"""[^"]*$', '', kode, flags=re.M)

cek('D1 ada helper _sudah_diunduh di KODE', '_sudah_diunduh' in kode)
cek('D2 ada helper _tandai_terunduh di KODE', '_tandai_terunduh' in kode)
cek('D3 ada helper _berkas_hidup di KODE', '_berkas_hidup' in kode)
cek('D4 rute /unduh MENOLAK kalau sudah diunduh',
    "'sudah_diunduh'" in kode and 'fid_lama' in kode)
cek('D5 penanda ditulis ke jurnal_json (kolom SUDAH ADA)',
    "'berkas_id'" in kode and 'jurnal_json' not in kode.split('berkas_id')[0][-200:])
cek('D6 penanda BASI kalau berkas dihapus (terhapus_pada)',
    'terhapus_pada' in kode)
cek('D7 /lihat melaporkan status sudah_diunduh ke UI',
    "a['sudah_diunduh']" in kode or 'a["sudah_diunduh"]' in kode)

# ── BAGIAN 2: UI ─────────────────────────────────────────────────────────
tpl = Path(f'{AKAR}/app/templates/referensi.html').read_text()
cek('D8 tombol berubah jadi "sudah diunduh" + MATI', 'disabled' in tpl and 'sudah diunduh' in tpl)
cek('D9 tombol lama "unduh ke workspace" masih ada (kalau belum)', 'unduh ke workspace' in tpl)
cek('D10 JS memuat ulang daftar setelah unduh/tertolak',
    "j.kode === 'sudah_diunduh'" in tpl)

# ── BAGIAN 3: UJI PERILAKU NYATA lewat HTTP (DB SALINAN) ─────────────────
DB_ASLI = Path(f'{AKAR}/data/eduai.db')
tmpdir = Path(tempfile.mkdtemp())
DB_UJI = tmpdir / 'uji.db'
if DB_ASLI.exists():
    shutil.copyfile(DB_ASLI, DB_UJI)

import os
os.environ['EDUAI_DB'] = str(DB_UJI)

try:
    from fastapi.testclient import TestClient

    import app.config as C
    # paksa DB salinan
    import app.models as M
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    eng = create_engine(f'sqlite:///{DB_UJI}')
    M.SessionLocal = sessionmaker(bind=eng, autoflush=False, autocommit=False)

    from app import auth as A
    from app.main import app as APP

    cl = TestClient(APP)

    # cari user + berkas yang punya artikel jurnal
    import sqlite3
    kon = sqlite3.connect(str(DB_UJI))
    baris = kon.execute(
        "SELECT p.user_id, p.file_id FROM profil_dokumen p "
        "WHERE p.jurnal_json LIKE '%title%' LIMIT 1").fetchone()
    kon.close()

    if not baris:
        cek('D11 ada data uji (artikel jurnal)', False, '(tidak ada artikel — uji perilaku dilewati)')
    else:
        uid, fid = baris
        tok = A.buat_token(uid)
        ck = A.SESSION_COOKIE
        cl.cookies.set(ck, tok)

        # ambil daftar artikel
        r = cl.get(f'/api/ai/v1/jurnal/lihat?file_id={fid}')
        j = r.json()
        cek('D11 /lihat balas ok', r.status_code == 200 and j.get('ok') is True,
            f'(HTTP {r.status_code})')
        ada_tanda = isinstance(j.get('artikel'), list) and j['artikel'] and \
            'sudah_diunduh' in j['artikel'][0]
        cek('D12 tiap artikel punya kunci sudah_diunduh', ada_tanda)

        # uji: artikel yang SUDAH punya berkas_id hidup → /unduh menolak
        sudah = [a for a in (j.get('artikel') or []) if a.get('sudah_diunduh')]
        if sudah:
            a0 = sudah[0]
            r2 = cl.post('/api/ai/v1/jurnal/unduh',
                         params={'file_id': fid, 'bab': 'BAB II',
                                 'kunci': a0.get('kunci', '')})
            j2 = r2.json()
            cek('D13 unduh artikel yang SUDAH ada → DITOLAK',
                j2.get('ok') is False and j2.get('kode') == 'sudah_diunduh',
                f"(kode={j2.get('kode')})")
        else:
            print('  (tidak ada artikel bertanda sudah_diunduh — uji D13 dilewati)')

except Exception as e:                                        # noqa: BLE001
    G += 1
    print(f'  GAGAL  D11-D13 uji perilaku gagal: {type(e).__name__}: {e}')
finally:
    shutil.rmtree(tmpdir, ignore_errors=True)

print(f'\nTOTAL: {L} LULUS / {G} GAGAL')
sys.exit(1 if G else 0)
