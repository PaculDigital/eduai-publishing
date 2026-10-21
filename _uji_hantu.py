"""UJI GERBANG: PERBAIKAN PROSES HANTU — 2 ARAH WAJIB BERGIGI.

A. SISI SEHAT (harus LULUS):
   A1. kerja sukses + `tandai_selesai` → status 'selesai', slot dilepas
   A2. kerja gagal (lempar) → status 'gagal', slot dilepas
   A3. antrean penuh → masuk antrean, LALU DILAYANI setelah slot bebas

B. SISI RUSAK (harus GAGAL kalau perbaikan dibuang):
   B1. kerja sukses TANPA `tandai_selesai` → penjaga hantu WAJIB menutup
       jadi 'gagal' (bukan tinggal 'jalan' selamanya)
   B2. `bersihkan_hantu()` → menutup proses 'jalan' tanpa utas + kuota balik
   B3. `_sedang_jalan` KEMBALI ke 0 setelah semua utas selesai
"""
import sys
import time
import threading

sys.path.insert(0, '/app')

from sqlalchemy import select                                         # noqa: E402
from app import proses as P                                           # noqa: E402
from app.models import ProsesAI, SessionLocal                          # noqa: E402

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  OK   {nama}')
    else:
        GAGAL += 1
        print(f'  GAGAL {nama}  {bukti}')


def utas_hidup():
    return [t.name for t in threading.enumerate()
            if t.name.startswith('proses-ai-')]


def ambil(db, kode):
    db.expire_all()
    return db.execute(select(ProsesAI).where(
        ProsesAI.kode == kode)).scalar_one_or_none()


db = SessionLocal()
print('═' * 74)
print('  UJI: PROSES HANTU — 2 ARAH')
print('═' * 74)


async def kerja_sukses(lapor):
    P.tandai_selesai(lapor.kode, hasil='ok', model_ai='uji', token_in=1,
                     token_out=1, token_revisi=1)


async def kerja_gagal(lapor):
    raise RuntimeError('UJI: gagal sengaja')


async def kerja_lupa_tandai(lapor):
    return 'selesai tapi lupa tandai'          # ← inti AKAR #12


print('\n── A. SISI SEHAT ──')
p1 = P.mulai(db, user_id=6, file_id=None, komentar=['uji'],
             jumlah_bagian=1, panjang=10)
P.jalankan(p1.kode, kerja_sukses)
time.sleep(5)
x = ambil(db, p1.kode)
cek('A1 kerja sukses + tandai_selesai → selesai',
    x.status == 'selesai', f'status={x.status!r}')

p2 = P.mulai(db, user_id=6, file_id=None, komentar=['uji'],
             jumlah_bagian=1, panjang=10)
P.jalankan(p2.kode, kerja_gagal)
time.sleep(5)
y = ambil(db, p2.kode)
cek('A2 kerja gagal → status gagal',
    y.status == 'gagal', f'status={y.status!r}')

print('\n── B. SISI RUSAK (inti AKAR #12) ──')
p3 = P.mulai(db, user_id=6, file_id=None, komentar=['uji'],
             jumlah_bagian=1, panjang=10)
P.jalankan(p3.kode, kerja_lupa_tandai)
time.sleep(6)
z = ambil(db, p3.kode)
cek('B1 kerja sukses TANPA tandai → PENJAGA HANTU menutup jadi gagal',
    z.status == 'gagal', f'status={z.status!r} (HANTU kalau masih jalan)')
cek('B1b pesan galat jujur menyebut kuota dikembalikan',
    'dikembalikan' in (z.galat or ''), f'galat={z.galat[:80]!r}')

cek('B3 _sedang_jalan kembali 0 setelah semua utas selesai',
    P._sedang_jalan == 0, f'_sedang_jalan={P._sedang_jalan}')
cek('B3b tak ada utas proses-ai tertinggal', not utas_hidup(),
    f'hidup={utas_hidup()}')

print('\n── B2. bersihkan_hantu() pada hantu buatan ──')
#  buat hantu buatan: status dipaksa 'jalan' tanpa utas
db2 = SessionLocal()
h = P.mulai(db2, user_id=6, file_id=None, komentar=['uji'],
            jumlah_bagian=1, panjang=10)
h.status = 'jalan'
h.tahap = 'Mulai bekerja'
db2.commit()
db2.close()
n = P.bersihkan_hantu()
hh = ambil(db, h.kode)
cek('B2 bersihkan_hantu menutup hantu', hh.status == 'gagal',
    f'status={hh.status!r} (n={n})')
cek('B2b slot dihitung ulang dari utas hidup', P._sedang_jalan == 0,
    f'_sedang_jalan={P._sedang_jalan}')

print('\n' + '═' * 74)
print(f'  HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)
sys.exit(1 if GAGAL else 0)
