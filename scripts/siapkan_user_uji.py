"""SIAPKAN prasyarat uji gempur: user uji e2e + berkas uji.

Kenapa: user `uji-berbayar-e2e@test.local` terhapus saat bersih-bersih
27Sep sore → 3 uji mati "user uji tidak ada" + gerbang_uji bilang
"user uji direset ✅" padahal UPDATE user_id=6 tiada = PESAN PALSU.
Skrip ini IDEMPOTEN (buat kalau tiada, pakai kalau ada).
Dijalankan: docker cp → docker exec -e PYTHONPATH=/app python /tmp/siapkan_user_uji.py
"""
import sys

sys.path.insert(0, '/app')
from datetime import datetime, timezone                      # noqa: E402
from app.models import SessionLocal, User, FileBerkas         # noqa: E402
from sqlalchemy import select                                 # noqa: E402

EMAIL = 'uji-berbayar-e2e@test.local'
NASKAH = '/app/_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx'

db = SessionLocal()
u = db.execute(select(User).where(User.email == EMAIL)).scalar_one_or_none()

if u is None:
    u = User(
        email=EMAIL, password_hash='uji-e2e-nonaktif-login',
        nama='Uji Berbayar E2E', kuota_mb=500, role='client', aktif=True,
        dibuat=datetime.now(timezone.utc), paket='penulis',
        nama_lengkap='Uji Berbayar E2E', nim='9999999',
        nama_kampus='Universitas Uji',
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    print(f'dibuat: user uji id={u.id} paket={u.paket}')
else:
    print(f'ada  : user uji id={u.id} paket={u.paket}')

#  Berkas uji (fisik disalin dulu kalau belum ada)
import os, shutil                                            # noqa: E402
naskah = db.execute(
    select(FileBerkas)
    .where(FileBerkas.user_id == u.id, FileBerkas.terhapus_pada.is_(None))
    .order_by(FileBerkas.id.desc())
).scalars().first()
if naskah is None:
    dst_dir = f'/app/uploads/{u.id}'
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, 'SKRIPSI-S1-unmul-fazrigading.docx')
    if not os.path.isfile(dst):
        shutil.copy(NASKAH, dst)
    naskah = FileBerkas(
        user_id=u.id, nama='SKRIPSI S1 uji.docx',
        nama_simpan='SKRIPSI-S1-unmul-fazrigading.docx',
        ukuran=os.path.getsize(dst),
        tipe='application/vnd.openxmlformats-officedocument.'
             'wordprocessingml.document',
        dibuat=datetime.now(timezone.utc), diubah=datetime.now(timezone.utc),
    )
    db.add(naskah)
    db.commit()
    db.refresh(naskah)
    print(f'dibuat: berkas uji id={naskah.id}')
else:
    print(f'ada  : berkas uji id={naskah.id}')

print(f'SIAP → user={u.id} file={naskah.id}')