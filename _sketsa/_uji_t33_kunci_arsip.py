#!/usr/bin/env python3
"""Uji Tahap 3.3 — KUNCI NASKAH + ARSIP >60 HARI (ACC Bos 06Okt26 "A").

Dijalankan DI DALAM container (docker exec). Memakai SALINAN DB, bukan
DB produksi — supaya tidak mengotori data nyata.

Menguji PERILAKU, bukan sekadar "fungsi ada":
  K1 kunci() tolak kalau belum selesai & tanpa paksa
  K2 kunci(paksa=True) tetap jalan + catatan TIDAK dihapus
  K3 buka_kunci() memulihkan
  K4 status_kunci() melaporkan belum_selesai dengan benar
  A1 catatan selesai & TUA → hilang dari daftar utama
  A2 catatan selesai & BARU → tetap tampil
  A3 catatan BELUM selesai & tua → TETAP tampil (jangan sembunyikan)
  A4 semuanya=True → arsip ikut tampil
"""
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, '/app')

# ── Siapkan salinan DB ────────────────────────────────────────────────
ASLI = '/app/data/eduai.db'
TMP = tempfile.mkdtemp(prefix='uji33-')
SALIN = os.path.join(TMP, 'eduai.db')
shutil.copy2(ASLI, SALIN)
os.environ['EDUAI_DATA_DIR'] = TMP

from sqlalchemy import create_engine                       # noqa: E402
from sqlalchemy.orm import sessionmaker                     # noqa: E402
import app.models as M                                      # noqa: E402
import app.pembimbing as P                                  # noqa: E402
from app.config import ARSIP_HARI                           # noqa: E402

engine = create_engine(f'sqlite:///{SALIN}')
M.Base.metadata.create_all(engine)
#  Migrasi kolom tambahan (idempoten) — memakai engine SALINAN.
with engine.connect() as _c:
    ada = {r[1] for r in _c.exec_driver_sql('PRAGMA table_info(pembimbingan)')}
    if 'terkunci_pada' not in ada:
        _c.exec_driver_sql('ALTER TABLE pembimbingan ADD COLUMN terkunci_pada DATETIME')
    if 'terkunci_oleh' not in ada:
        _c.exec_driver_sql('ALTER TABLE pembimbingan ADD COLUMN terkunci_oleh INTEGER DEFAULT 0')
    _c.commit()
Sesi = sessionmaker(bind=engine)
db = Sesi()

lulus, gagal = [], []


def cek(nama, syarat, info=''):
    (lulus if syarat else gagal).append(nama)
    print(f"  {'✅' if syarat else '❌'} {nama}" + (f"  [{info}]" if info else ''))


# ── Siapkan bimbingan uji ─────────────────────────────────────────────
bim = db.query(M.Pembimbingan).first()
if bim is None:
    print('❌ Tidak ada baris pembimbingan di DB — uji tidak bisa jalan.')
    sys.exit(1)
BID = bim.id
print(f'  (bimbingan uji id={BID})\n')

# bersihkan kolom kunci dulu
bim.terkunci_pada = None
bim.terkunci_oleh = 0

# catatan uji milik bimbingan ini
def buat_catatan(warna, sudah_oke=None, dilewati=0):
    c = M.CatatanPembimbing(
        pembimbingan_id=BID, berkas_id=None, penulis_id=None,
        ronde=1, section_id='1.1', section_judul='Latar Belakang',
        teks_asli='x', warna=warna, isi='catatan uji', keadaan='utuh',
        sudah_oke=sudah_oke, dibuang=0, dilewati=dilewati,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

tua = P._sekarang() - timedelta(days=ARSIP_HARI + 5)
baru = P._sekarang() - timedelta(days=2)

c_kuning = buat_catatan('kuning')                     # belum selesai
c_sel_tua = buat_catatan('hijau', sudah_oke=tua)      # selesai + TUA
c_sel_baru = buat_catatan('hijau', sudah_oke=baru)    # selesai + BARU
c_lewati = buat_catatan('kuning', dilewati=1)         # kuning tapi dilewati

print('── KUNCI NASKAH ──')
s = P.status_kunci(db, BID)
cek('K1 status awal belum terkunci', s['terkunci'] is False)
cek('K1 belum_selesai menghitung hanya kuning-bukan-dilewati',
    s['belum_selesai'] == 1, f"dapat {s['belum_selesai']}")

h = P.kunci(db, BID, oleh_pembimbing=False, paksa=False)
cek('K2 kunci() tanpa paksa → butuh konfirmasi', h.get('butuh_konfirmasi') is True)
bim2 = db.get(M.Pembimbingan, BID)
cek('K2 belum benar-benar terkunci saat butuh konfirmasi',
    bim2.terkunci_pada is None)

h = P.kunci(db, BID, oleh_pembimbing=False, paksa=True)
cek('K3 kunci(paksa=True) → berhasil', h.get('ok') is True and h.get('terkunci') is True)
db.expire_all()
bim3 = db.get(M.Pembimbingan, BID)
cek('K3 DB mencatat terkunci_pada', bim3.terkunci_pada is not None)
n_cat = db.query(M.CatatanPembimbing).filter(
    M.CatatanPembimbing.pembimbingan_id == BID).count()
cek('K3 catatan TIDAK dihapus saat dikunci', n_cat >= 4, f'{n_cat} catatan')

h = P.buka_kunci(db, BID)
db.expire_all()
bim4 = db.get(M.Pembimbingan, BID)
cek('K4 buka_kunci() memulihkan', h.get('ok') is True and bim4.terkunci_pada is None)

print('\n── ARSIP >60 HARI ──')
daftar = P.daftar_catatan(db, BID)                    # daftar utama
ids = {c.id for c in daftar}
cek('A1 catatan selesai+TUA tersembunyi', c_sel_tua.id not in ids)
cek('A2 catatan selesai+BARU tetap tampil', c_sel_baru.id in ids)
cek('A3 catatan belum-selesai walau tua TETAP tampil', c_kuning.id in ids)
cek('A3 kuning-dilewati tetap tampil', c_lewati.id in ids)

penuh = P.daftar_catatan(db, BID, semuanya=True)
ids_penuh = {c.id for c in penuh}
cek('A4 semuanya=True → arsip ikut tampil', c_sel_tua.id in ids_penuh)

# bersihkan
for c in (c_kuning, c_sel_tua, c_sel_baru, c_lewati):
    db.delete(c)
db.commit()
db.close()
shutil.rmtree(TMP, ignore_errors=True)

print(f"\n═══ HASIL: {len(lulus)} LULUS / {len(gagal)} GAGAL ═══")
if gagal:
    for g in gagal:
        print('  ❌', g)
    sys.exit(1)
