"""GERBANG — LINK JURNAL.txt (putusan Bos A1/B2/C/D, 06Okt26).

Menguji rute `/link-jurnal` LEWAT HTTP NYATA (TestClient) di DB SALINAN.

CARA PAKAI (DI DALAM container):
    docker cp _gerbang_link_jurnal.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _gerbang_link_jurnal.py
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

cek('L1 ada fungsi perakit teks', '_rakit_teks_link_jurnal' in kode)
cek('L2 ada penyimpan .txt (pola dokumen_baru)', '_simpan_teks_berkas' in kode)
cek('L3 ada rute /link-jurnal', "@router.post('/link-jurnal')" in kode)
cek('L4 nama berkas ".txt" (bukan .md — belum diizinkan)',
    "'Link Jurnal.txt'" in kode or 'Link Jurnal.txt' in src)
cek('L5 tipe berkas text/plain', "text/plain" in kode)
cek('L6 nama_simpan unik (token_hex) — tidak menimpa',
    'token_hex' in kode and '.txt' in kode.split('token_hex')[-1][:12])
#  L7: periksa HANYA di dalam fungsi BARU (bukan seluruh berkas — fungsi lain
#  memang menulis ke jurnal; yang penting fungsi ini TIDAK menulis balik).
_awal = kode.find('def _rakit_teks_link_jurnal')
_akhir = kode.find('@router.post(\'/hapus\')')
_badan = kode[_awal:_akhir] if (_awal >= 0 and _akhir > _awal) else ''
cek('L7 A1: fungsi baru membaca jurnal, TIDAK menulis balik',
    '_jurnal.baca' in _badan and '_jurnal.tulis' not in _badan,
    f'(baca={_badan.count("_jurnal.baca")}, tulis={_badan.count("_jurnal.tulis")})')
cek('L8 C: satu nama tetap (konstanta)',
    'NAMA_LINK_JURNAL' in kode)
cek('L9 D: kembar lama dibuang ke tong sampah',
    'ke_sampah' in kode)

# B2: folder.buat() TIDAK boleh disentuh
fld = Path(f'{AKAR}/app/folder.py').read_text()
cek('L10 B2: berkas TIDAK dibuat saat folder dibuat',
    'Link Jurnal' not in fld and 'link_jurnal' not in fld)

# ── BAGIAN 2: UJI PERILAKU NYATA (HTTP, DB salinan) ──────────────────────
DB_ASLI = Path(f'{AKAR}/data/eduai.db')
tmp = Path(tempfile.mkdtemp())
DB = tmp / 'uji.db'
shutil.copyfile(DB_ASLI, DB)

import sqlite3                                             # noqa: E402

from sqlalchemy import create_engine                       # noqa: E402
from sqlalchemy.orm import sessionmaker                    # noqa: E402

import app.models as M                                     # noqa: E402
eng = create_engine(f'sqlite:///{DB}')
M.SessionLocal = sessionmaker(bind=eng, autoflush=False, autocommit=False)

from app import auth as A                                  # noqa: E402
from app.main import app as APP                            # noqa: E402

try:
    from fastapi.testclient import TestClient
    cl = TestClient(APP)

    kon = sqlite3.connect(str(DB))
    baris = kon.execute(
        "SELECT p.user_id, p.file_id FROM profil_dokumen p "
        "WHERE p.jurnal_json LIKE '%title%' LIMIT 1").fetchone()
    uji_uid = baris[0] if baris else 8
    #  Ambil naskah milik user (yang punya folder jg kalau ada)
    fb = kon.execute(
        "SELECT id FROM files WHERE user_id=? AND terhapus_pada IS NULL "
        "ORDER BY id LIMIT 1", (uji_uid,)).fetchone()
    kon.close()

    cek('L11 ada naskah uji', fb is not None)
    fid = fb[0]

    tok = A.buat_token(uji_uid)
    cl.cookies.set(A.SESSION_COOKIE, tok)

    #  ── Panggil rute ────────────────────────────────────────────────────
    r = cl.post('/api/ai/v1/jurnal/link-jurnal',
                params={'file_id': fid, 'folder_id': 0})
    j = r.json()
    cek('L12 rute balas ok', r.status_code == 200 and j.get('ok') is True,
        f"(HTTP {r.status_code}, ok={j.get('ok')})")
    cek('L13 nama berkas = "Link Jurnal.txt"',
        (j.get('nama') or '') == 'Link Jurnal.txt', f"({j.get('nama')})")
    cek('L14 ukuran > 0', (j.get('ukuran') or 0) > 0, f"({j.get('ukuran')} byte)")

    #  ── Berkas BENAR-BENAR ada di disk ──────────────────────────────────
    #  ⚠️ JEBAKAN: `UPLOAD_DIR` = `/app/uploads` (BUKAN `/app/data/unggah`).
    #  Ambil dari config supaya tidak salah ukur kalau lokasi berubah.
    from app.config import UPLOAD_DIR as _UD
    kon = sqlite3.connect(str(DB))
    row = kon.execute(
        "SELECT nama_simpan, user_id FROM files WHERE id=?",
        (j.get('file_id'),)).fetchone()
    kon.close()
    nama_simpan = row[0] if row else None
    pemilik = row[1] if row else None
    berkas = Path(f'{_UD}/{pemilik}/{nama_simpan}')
    cek('L15 berkas .txt NYATA di disk (berkas_id baru)', j.get('file_id') is not None
        and nama_simpan is not None, f"(id={j.get('file_id')})")
    cek('L16 berkas benar-benar ditulis', berkas.is_file(), f"({berkas})")

    isi = berkas.read_text(encoding='utf-8') if berkas.is_file() else ''
    cek('L17 isi memuat judul LINK JURNAL', 'LINK JURNAL' in isi)
    cek('L18 isi memuat minimal 1 artikel', 'Total: ' in isi)
    cek('L19 isi memuat tautan', 'Gratis:' in isi or 'Penerbit:' in isi
        or 'Tautan:' in isi)
    cek('L20 TIDAK memuat simbol emoji (aman utk .txt)',
        not any(ch in isi for ch in ('🟢', '🔒')))
    cek('L21 ada keterangan "dibuat otomatis" (A1 jujur)',
        'dibuat otomatis' in isi)

    #  ── D: tekan LAGI → berkas BARU, yang lama masuk tong sampah ────────
    r2 = cl.post('/api/ai/v1/jurnal/link-jurnal',
                 params={'file_id': fid, 'folder_id': 0})
    j2 = r2.json()
    cek('L22 tekan lagi → dibuat ULANG (file_id baru)',
        j2.get('ok') is True and j2.get('file_id') != j.get('file_id'),
        f"({j.get('file_id')} → {j2.get('file_id')})")

    kon = sqlite3.connect(str(DB))
    kembar = kon.execute(
        "SELECT COUNT(*) FROM files WHERE user_id=? AND nama='Link Jurnal.txt' "
        "AND terhapus_pada IS NULL", (uji_uid,)).fetchone()[0]
    kon.close()
    cek('L23 hanya SATU berkas hidup (tidak menumpuk)', kembar == 1,
        f'(jumlah={kembar})')

    #  ── D: tekan lagi setelah itu → tetap bisa (berkas lama → sampah) ───
    r3 = cl.post('/api/ai/v1/jurnal/link-jurnal',
                 params={'file_id': fid, 'folder_id': 0})
    cek('L24 dibuat lagi berkali-kali tetap OK', r3.json().get('ok') is True)

except Exception as e:                                     # noqa: BLE001
    G += 1
    print(f'  GAGAL  L11-L24 uji perilaku gagal: {type(e).__name__}: {e}')
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f'\nTOTAL: {L} LULUS / {G} GAGAL')
sys.exit(1 if G else 0)
