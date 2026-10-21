"""ANALISA CELAH paket GRATIS (3 revisi) — uji dengan angka NYATA.

Pertanyaan Bos: kalau 1 revisi = 55.000 karakter, apakah gratis bisa
menyelesaikan sampai BAB III?

Uji: pakai tesis Bos (TESIS_LENGKAP_Goras.docx) di user uji (paket gratis),
hitung: berapa bab terdeteksi, panjang tiap bab, berapa bagian (=revisi)
per bab, dan berapa bab yang BISA diselesaikan dengan 3 revisi.
"""
import subprocess

EMAIL = 'uji-gratis-render@test.local'


def di(py):
    r = subprocess.run(['docker', 'exec', 'eduai-app', 'python3', '-c', py],
                       capture_output=True, text=True, timeout=180)
    return (r.stdout or '').strip(), (r.stderr or '').strip()


# Salin tesis Bos ke user uji sebagai bahan hitung (TIDAK mengubah milik Bos)
out, err = di(f"""
import sys, shutil, os; sys.path.insert(0,'/app')
from app.models import SessionLocal, User, FileBerkas
from app.config import UPLOAD_DIR
from sqlalchemy import select
db = SessionLocal()
bos = db.scalars(select(FileBerkas).where(FileBerkas.nama.like('%TESIS%'))).first()
uji = db.scalars(select(User).where(User.email=='{EMAIL}')).first()
print('berkas acuan:', bos.nama if bos else None, (bos.ukuran if bos else 0), 'byte')
if bos:
    d = UPLOAD_DIR / str(uji.id); d.mkdir(parents=True, exist_ok=True)
    src = UPLOAD_DIR / str(bos.user_id) / bos.nama_simpan
    dst = d / 'acuan_tesis.docx'
    if os.path.exists(src):
        shutil.copy(src, dst)
        print('disalin:', dst, os.path.getsize(dst), 'byte')
    else:
        print('SUMBER TIDAK ADA di disk:', src)
db.close()
""")
print(out or err[:400])
