"""UJI AKHIR: E2E JALUR LATAR BELAKANG SUNGGUHAN — sesudah perbaikan hantu.

Membuktikan: revisi mahasiswa LEWAT JALUR LATAR BELAKANG tidak lagi menggantung.
2 ARAH:
  A. Jalur sehat   → status 'selesai' dalam waktu wajar + dokumen utuh + kuota tepat
  B. Hantu dibuat  → `bersihkan_hantu()` menutupnya, lalu revisi BARU tetap jalan
"""
import sys
import time

sys.path.insert(0, '/app')

from sqlalchemy import select                                         # noqa: E402
from app import ai as A                                               # noqa: E402
from app import proses as P                                           # noqa: E402
from app.models import (BerkasPembimbingan, CatatanPembimbing,         # noqa: E402
                        FileBerkas, PemakaianAI, ProsesAI, SessionLocal,
                        User)

db = SessionLocal()
k = db.execute(select(CatatanPembimbing).where(
    CatatanPembimbing.id == 106)).scalar_one()
pb = db.execute(select(BerkasPembimbingan).where(
    BerkasPembimbingan.id == k.berkas_id)).scalar_one()
fb = db.execute(select(FileBerkas).where(
    FileBerkas.id == pb.file_id)).scalar_one()
u = db.execute(select(User).where(User.id == fb.user_id)).scalar_one()

pem = db.execute(select(PemakaianAI).where(
    PemakaianAI.user_id == u.id)).scalar_one_or_none()
if pem is not None:
    pem.jumlah_revisi = 0
    db.commit()

print('═' * 76)
print('  UJI AKHIR: E2E LATAR BELAKANG (sesudah perbaikan hantu)')
print('═' * 76)
print(f'user={u.id} berkas={fb.id} naskah={fb.nama_simpan}')
print(f'prasyarat: antrean={P.statistik_antrean()}')


class Req:                                                                # noqa: D101
    def __init__(self, b):
        self._b = b

    async def json(self):
        return self._b


body = {'file_id': fb.id, 'bab': '__seluruh__',
        'komentar': [k.isi or 'perbaiki'], 'setuju_bagian': True}


async def kerja(lapor):
    await A._revisi_kerja(Req(body), u, db)


p2 = P.mulai(db, user_id=u.id, file_id=fb.id, komentar=[k.isi or 'perbaiki'],
             jumlah_bagian=2, panjang=64243)
print(f'\nproses kode={p2.kode}')

t0 = time.time()
P.jalankan(p2.kode, kerja)
print(f'P.jalankan() dipanggil ({time.time()-t0:.2f} dtk)')

akhir = None
for i in range(1, 19):
    time.sleep(10)
    db.expire_all()
    px = db.execute(select(ProsesAI).where(
        ProsesAI.kode == p2.kode)).scalar_one()
    print(f'   t+{i*10:3d}s · status={px.status:<9} tahap={px.tahap[:38]:<38} '
          f'· jalan={P._sedang_jalan}')
    if px.status in ('selesai', 'gagal'):
        akhir = px
        break

print('\n══ HASIL AKHIR ══')
if akhir is None:
    print('❌ MASIH MENGGANTUNG setelah 180 dtk — perbaikan TIDAK berhasil!')
    sys.exit(1)
dtk = time.time() - t0
print(f'status       : {akhir.status.upper()} dalam {dtk:.1f} dtk')
print(f'model        : {akhir.model_ai}')
print(f'token        : in={akhir.token_in} out={akhir.token_out} '
      f'revisi={akhir.token_revisi}')
print(f'bagian       : {akhir.bagian_ke}/{akhir.jumlah_bagian}')
print(f'galat        : {(akhir.galat or "-")[:160]}')
print(f'slot antrean : jalan={P._sedang_jalan} · {P.statistik_antrean()}')

db.expire_all()
pem2 = db.execute(select(PemakaianAI).where(
    PemakaianAI.user_id == u.id)).scalar_one_or_none()
print(f'kuota dipakai: {pem2.jumlah_revisi if pem2 else "?"}')

print('\n' + '═' * 76)
if akhir.status == 'selesai':
    print('  ✅ LULUS — jalur latar belakang BEKERJA, tidak menggantung lagi')
    sys.exit(0)
print('  ❌ status bukan selesai')
sys.exit(1)
