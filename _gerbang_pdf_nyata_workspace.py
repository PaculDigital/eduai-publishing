"""UJI NYATA — PDF SUNGGUHAN dari internet → tersimpan ke workspace.

Ini uji PEMBUKTIAN BUG (sebelum perbaikan, artikel terbuka SELALU gagal).
Dijalankan DI DALAM container (butuh jaringan + httpx).
Memakai DB SALINAN + folder unggah SALINAN (produksi tidak disentuh).
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

TMP = tempfile.mkdtemp(prefix='uji_pdf_nyata_')
DB = os.path.join(TMP, 'uji.db')
UPL = os.path.join(TMP, 'uploads')
shutil.copyfile('/app/data/eduai.db', DB)
os.environ['EDUAI_DB'] = DB
os.environ['EDUAI_UPLOAD_DIR'] = UPL

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app import models as M  # noqa: E402

eng = create_engine(f'sqlite:///{DB}', connect_args={'check_same_thread': False})
M.engine = eng
M.SessionLocal = sessionmaker(bind=eng, expire_on_commit=False)

from app import pustaka as P  # noqa: E402
from app import rute_jurnal as RJ  # noqa: E402

URL = ('https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/'
       'dummy.pdf')

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
fk = M.Folder(user_id=u.id, nama='WS-Uji-PDF-Nyata', warna='hijau')
db.add(fk)
db.commit()
db.refresh(fk)

#  ── 1. Ambil PDF sungguhan lewat MESIN (pustaka) ─────────────────────────
hasil = P.unduh_pdf({'title': 'Dummy Paper', 'year': 2021, 'pdf_url': URL})
cek('P1 mesin berhasil ambil PDF nyata', hasil.get('ok') is True,
    f'(kunci={sorted(hasil)})')
cek('P2 mesin balas "isi" byte PDF (BUKAN "berkas")',
    isinstance(hasil.get('isi'), bytes) and hasil.get('isi')[:4] == b'%PDF')
cek('P3 ukuran masuk akal (>1KB)', (hasil.get('ukuran') or 0) > 1024,
    f'({hasil.get("ukuran")} byte)')

#  ── 2. Simpan ke workspace ───────────────────────────────────────────────
target = {'title': 'Dummy Paper', 'year': 2021, 'pdf_url': URL}
out = RJ._simpan_pdf(db, u, target, hasil, folder_id=fk.id)
cek('P4 tersimpan ke workspace (ok=True)', bool(out.get('ok')),
    f'({out.get("pesan", "")[:50]})')
cek('P5 folder_id = workspace pilihan', out.get('folder_id') == fk.id)

fb = db.get(M.FileBerkas, out.get('file_id')) if out.get('file_id') else None
cek('P6 baris `files` tercatat', fb is not None)
if fb:
    from pathlib import Path
    jal = Path(UPL) / str(u.id) / fb.nama_simpan
    cek('P7 berkas NYATA di disk', jal.exists(),
        f'({jal.stat().st_size if jal.exists() else 0} byte)')
    cek('P8 isi disk == PDF terunduh',
        jal.exists() and jal.read_bytes() == hasil.get('isi'))
    cek('P9 nama tampil rapi (*.pdf)', fb.nama.endswith('.pdf'), f'({fb.nama})')
    #  ── 3. Bukti PEMBUKTIAN BUG: kode lama akan menolak di sini ───────────
    cek('P10 ⭐ BUKTI BUG LAMA SEMBUH: artikel terbuka TIDAK ditolak lagi',
        bool(out.get('ok')) and fb.folder_id is not None)

db.close()
print(f'\nTOTAL: {L} LULUS / {G} GAGAL')
sys.exit(1 if G else 0)
