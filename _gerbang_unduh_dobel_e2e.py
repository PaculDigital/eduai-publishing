"""UJI PERILAKU NYATA — alur LENGKAP syarat Bos (unduh → dobel ditolak → hapus → boleh lagi).

Memakai DB SALINAN + PDF SUNGGUHAN dari internet. Dijalankan DI DALAM container.

    docker cp _gerbang_unduh_dobel_e2e.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _gerbang_unduh_dobel_e2e.py
"""
from __future__ import annotations

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


DB_ASLI = Path(f'{AKAR}/data/eduai.db')
tmp = Path(tempfile.mkdtemp())
DB = tmp / 'uji.db'
shutil.copyfile(DB_ASLI, DB)

from sqlalchemy import create_engine                     # noqa: E402
from sqlalchemy.orm import sessionmaker                  # noqa: E402

import app.models as M                                    # noqa: E402
eng = create_engine(f'sqlite:///{DB}')
M.SessionLocal = sessionmaker(bind=eng, autoflush=False, autocommit=False)

from app.models import FileBerkas, ProfilDokumen, SessionLocal, User   # noqa: E402
from app import jurnal as J                                # noqa: E402
from app import rute_jurnal as R                           # noqa: E402
from app import folder as F                               # noqa: E402

db = SessionLocal()

# ── Siapkan user + naskah + 1 artikel ber-PDF terbuka ──────────────────
u = db.query(User).filter(User.email.like('%asih%')).first()
cek('P1 user uji ditemukan', u is not None, f'({u.email if u else "-"})')

# naskah milik user
fb = (db.query(FileBerkas)
        .filter(FileBerkas.user_id == u.id, FileBerkas.terhapus_pada.is_(None))
        .first())
cek('P2 naskah uji ditemukan', fb is not None, f'({fb.nama if fb else "-"})')

prof = R._profil_atau_buat(db, fb.id, u.id)
db.commit()

PDF_UJI = 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'
KUNCI_UJI = 'doi:uji-dobel-0001'
artikel = {'title': 'ARTIKEL UJI DOBEL', 'authors': 'Wulan', 'year': 2026,
           'journal': 'Jurnal Uji', 'doi': 'uji-dobel-0001',
           'doi_status': 'verified', 'pdf_url': PDF_UJI, 'is_oa': True,
           'abstract': 'Abstrak uji.'}
d = J.baca(prof)
d = J.tambah(d, 'BAB II', artikel)      # ⚠️ tambah() MENGEMBALIKAN data baru
J.tulis(prof, d)
db.commit()

art = next((a for a in J.semua_artikel(J.baca(prof)) if J.kunci(a) == KUNCI_UJI), None)
cek('P3 artikel uji tersimpan', art is not None)
art['pdf_url'] = PDF_UJI
art['is_oa'] = True

# ── 1. SEBELUM unduh: TIDAK ditandai ───────────────────────────────────
cek('P4 sebelum unduh: belum ditandai sudah_diunduh',
    R._sudah_diunduh(db, art) == 0)

# ── 2. UNDUH (PDF nyata) ───────────────────────────────────────────────
from app import pustaka as P                              # noqa: E402
hasil = P.unduh_pdf(art)
cek('P5 mesin mengembalikan byte PDF (' + str(hasil.get('ukuran') or 0) + ' byte)',
    bool(hasil.get('ok') and hasil.get('isi')))

out = R._simpan_pdf(db, u, art, hasil, folder_id=0)
cek('P6 PDF tersimpan jadi berkas user', bool(out.get('ok') and out.get('file_id')),
    f"(file_id={out.get('file_id')})")
fid_baru = out.get('file_id')

# ── 3. SESUDAH unduh: DITANDAI ─────────────────────────────────────────
art2 = next((a for a in J.semua_artikel(J.baca(prof)) if J.kunci(a) == KUNCI_UJI), None)
cek('P7 penanda berkas_id ditulis ke artikel', bool(art2 and art2.get('berkas_id')))
cek('P8 _sudah_diunduh kini mengembalikan file_id',
    R._sudah_diunduh(db, art2) == fid_baru, f'({R._sudah_diunduh(db, art2)})')

# ── 4. COBA UNDUH DOBEL → HARUS DITOLAK ────────────────────────────────
fid_lama = R._sudah_diunduh(db, art2)
cek('P9 unduh dobel TERDETEKSI (akan ditolak rute)', bool(fid_lama))

# ── 5. HAPUS berkas (masuk tong sampah) → BOLEH unduh lagi ─────────────
from app import sampah as S                               # noqa: E402
fb_pdf = db.get(FileBerkas, fid_baru)
S.ke_sampah(db, fb_pdf)
db.commit()
db.refresh(fb_pdf)
cek('P10 berkas masuk tong sampah (terhapus_pada terisi)',
    fb_pdf.terhapus_pada is not None)

art3 = next((a for a in J.semua_artikel(J.baca(prof)) if J.kunci(a) == KUNCI_UJI), None)
setelah_hapus = R._sudah_diunduh(db, art3)
cek('P11 SETELAH dihapus: penanda BASI ⇒ BOLEH unduh lagi', setelah_hapus == 0,
    f'(kembali {setelah_hapus})')

# ── 6. UNDUH LAGI → berhasil, berkas BARU ──────────────────────────────
hasil2 = P.unduh_pdf(art3)
out2 = R._simpan_pdf(db, u, art3, hasil2, folder_id=0)
cek('P12 unduh ULANG berhasil (berkas baru, id beda)',
    bool(out2.get('ok')) and out2.get('file_id') != fid_baru,
    f"({fid_baru} → {out2.get('file_id')})")

# bersih
for x in db.query(FileBerkas).filter(FileBerkas.id.in_([fid_baru, out2.get('file_id') or 0])).all():
    try:
        x.nama_simpan and (Path(f'{AKAR}/data/unggah/{u.id}/{x.nama_simpan}').unlink(missing_ok=True))
    except Exception:                                     # noqa: BLE001
        pass
db.close()
shutil.rmtree(tmp, ignore_errors=True)

print(f'\nTOTAL: {L} LULUS / {G} GAGAL')
sys.exit(1 if G else 0)
