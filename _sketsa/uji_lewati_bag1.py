"""UJI LEWATI REVISI (Tahap 3.2, ACC Bos 24Sep26) — BAGIAN 1: MESIN.

Menguji fungsi SUNGGUHAN di app/pembimbing.py dengan DB SEMENTARA.

⚠️ PELAJARAN 24Sep26 (mahal, jangan ulang): uji PERTAMA Wulan menyentuh DB
   PRODUKSI (muncul 'UNIQUE constraint failed: users.email' + 1 user uji
   benar-benar masuk, terpaksa dihapus manual). AKAR: driver SQLAlchemy
   membaca DATABASE_URL saat impor; mengganti os.environ SETELAH impor app
   = terlambat. OBAT: set `EDUAI_DATA_DIR` ke folder sementara SEBELUM
   baris `from app import ...`.
"""
import os, sys, tempfile, shutil
from datetime import datetime, timedelta, timezone

#  ⚠️ WAJIB paling atas — sebelum impor app apa pun.
tmp = tempfile.mkdtemp(prefix='uji_lewati_')
os.environ['EDUAI_DATA_DIR'] = tmp
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(tmp, 'upload')
sys.path.insert(0, '/app')

LULUS, GAGAL = [], []


def cek(nama, syarat, ket=''):
    if syarat:
        LULUS.append(nama); print(f'  LULUS  {nama}')
    else:
        GAGAL.append(nama); print(f'  GAGAL  {nama}  {ket}')


from app import models as M
from app import pembimbing as P

#  PAGAR UJI: buktikan DB yang dipakai MEMANG sementara.
db_file = str(M.engine.url)
cek('P0 DB uji = folder sementara (BUKAN produksi)',
    tmp in db_file, db_file)

M.init_db()
db = M.SessionLocal()

#  ── siapkan data uji (urut: user → files → pembimbingan → catatan) ──
u = M.User(email='mhs@uji.id', password_hash='x', nama='Mhs Uji', paket='gratis')
db.add(u); db.commit()
f = M.FileBerkas(user_id=u.id, nama='Uji.docx', nama_simpan='uji.docx',
                 ukuran=1000, tipe='docx')
db.add(f); db.commit()
b = M.Pembimbingan(user_id=u.id, nama='Pembimbing Uji', token_sidik='x' * 32,
                   kedaluwarsa=datetime.now(timezone.utc) + timedelta(days=7))
db.add(b); db.commit()
#  ⚠️ PENTING: `pembimbingan_berkas` harus ada barisnya, kalau tidak
#  `catat()` gagal FK (terukur: 'FOREIGN KEY constraint failed').
bk = M.BerkasPembimbingan(pembimbingan_id=b.id, file_id=f.id,
                          judul='Uji.docx')
db.add(bk); db.commit()

c1 = P.catat(db, b, 'Perbaiki latar belakang, tambahkan data terbaru.',
             section_id='1.1', section_judul='Latar Belakang',
             teks_asli='Perbaiki latar belakang', mulai=0, akhir=10,
             berkas_id=f.id)
c1.penulis_id = u.id; db.commit()
print(f'data uji siap: catatan id={c1.id} berkas={c1.berkas_id}')
