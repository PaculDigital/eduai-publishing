#!/usr/bin/env python3
"""UJI PEMICU NOTIFIKASI OTOMATIS (ACC Bos 17Sep26).

MEMBUKTIKAN notifikasi benar-benar MUNCUL saat kejadiannya terjadi —
bukan hanya kalimat yang tersimpan rapi.

Yang diuji:
  1. Kuota menipis → notifikasi 'kuota_hampir_habis' TERCATAT
  2. Kuota masih banyak → DIAM (tidak mengganggu)
  3. Anti-spam → tidak dikirim 2× dalam 24 jam
  4. Notifikasi gagal → tidak pernah menggagalkan potongan kuota
  5. Endpoint lonceng menggabungkan 2 sumber
"""
import sys
sys.path.insert(0, '/app')
from app.models import SessionLocal, Notifikasi, User
from app import notifikasi as N
from sqlalchemy import select, delete

lulus = gagal = 0


def cek(nama, syarat, bukti=''):
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  ✅ {nama} {bukti}')
    else:
        gagal += 1
        print(f'  ❌ {nama} {bukti}')


db = SessionLocal()
u = db.execute(select(User).where(User.email == 'uji-berbayar-e2e@test.local')).scalar_one_or_none()
if u is None:
    print('❌ user uji tidak ada'); sys.exit(1)
UID = u.id
print(f'=== user uji id={UID} paket={u.paket} ===')

# bersihkan sisa
db.execute(delete(Notifikasi).where(Notifikasi.user_id == UID))
db.commit()

print('\n=== 1. KUOTA MENIPIS → TERCATAT ===')
#  Sisa 2 (sama dengan AMBANG_KUOTA) → harus tercatat
t1 = N.periksa_dan_catat(db, UID, sisa_kuota=2)
db.commit()
cek('sisa 2 memicu kuota_hampir_habis', 'kuota_hampir_habis' in t1,
    f'→ {t1}')
n1 = db.execute(select(Notifikasi).where(
    Notifikasi.user_id == UID,
    Notifikasi.jenis == 'kuota_hampir_habis')).scalars().all()
cek('tersimpan di tabel notifikasi', len(n1) == 1)
if n1:
    print(f'     judul: "{n1[0].judul}"')
    print(f'     isi  : "{n1[0].isi[:95]}"')
    print(f'     nada={n1[0].nada} tombol={n1[0].tombol}')
    cek('nada = ingat (lembut)', n1[0].nada == 'ingat')
    cek('tombol tersedia', bool(n1[0].tombol))
    cek('memakai sebutan EduAi / tidak ada "AI"',
        'EduAi' in n1[0].isi or 'AI' not in n1[0].isi.replace('EduAi', ''))

print('\n=== 2. KUOTA MASIH BANYAK → DIAM (tidak mengganggu) ===')
t2 = N.periksa_dan_catat(db, UID, sisa_kuota=20)
db.commit()
cek('sisa 20 TIDAK memicu apa pun', t2 == [], f'→ {t2}')

print('\n=== 3. ANTI-SPAM 24 JAM ===')
#  Coba lagi kondisi yang sama → harus DILEWATI
t3 = N.periksa_dan_catat(db, UID, sisa_kuota=2)
db.commit()
cek('sisa 2 kedua kali DILEWATI (anti-spam)', t3 == [], f'→ {t3}')
n_total = db.execute(select(Notifikasi).where(
    Notifikasi.user_id == UID)).scalars().all()
cek('tetap hanya 1 baris (tidak menumpuk)', len(n_total) == 1,
    f'(ada {len(n_total)})')

print('\n=== 4. NOTIFIKASI GAGAL TIDAK MENGGAGALKAN PEKERJAAN UTAMA ===')
#  🐛 AKAR YANG DIBUKTIKAN (17Sep26): `db.add()` gagal (user_id tidak sah →
#  FOREIGN KEY gagal) MERACUNI sesi SQLAlchemy → perintah berikutnya di sesi
#  yang sama melempar PendingRollbackError. Kalau dipakai di jalur produksi,
#  pekerjaan revisi user ikut error. Uji ini yang menjaganya.
db2 = SessionLocal()
try:
    hasil = N.catat(db2, 999999, 'revisi_selesai', file_id=1)
    cek('catat() user tidak sah TIDAK melempar', hasil is False, f'→ {hasil}')

    #  INI INTINYA: sesi harus TETAP SEHAT sesudah kegagalan di atas.
    try:
        cek('sesi tetap sehat sesudah gagal (tidak teracuni)', True)
        N.catat(db2, UID, 'pembayaran_masuk')       # harus jalan normal
        db2.commit()
        cek('notifikasi berikutnya di sesi SAMA tetap bisa disimpan', True)
    except Exception as e:
        cek('sesi tetap sehat sesudah gagal (tidak teracuni)', False,
            f'→ {type(e).__name__}: {str(e)[:90]}')
except Exception as e:
    cek('catat() user tidak sah TIDAK melempar', False,
        f'→ {type(e).__name__}: {e}')
finally:
    try:
        db2.close()
    except Exception:                                             # noqa: BLE001
        pass

#  jenis tidak dikenal juga tidak boleh melempar
db3 = SessionLocal()
try:
    hasil2 = N.catat(db3, UID, 'jenis_ngawur_xyz')
    cek('catat() jenis asing tidak melempar', True, f'→ {hasil2}')
    db3.commit()
except Exception as e:
    cek('catat() jenis asing tidak melempar', False,
        f'→ {type(e).__name__}: {e}')
finally:
    db3.close()

print('\n=== 5. NOTIFIKASI PEMBAYARAN (jenis non-proses) ===')
db.execute(delete(Notifikasi).where(Notifikasi.user_id == UID))
db.commit()
ok = N.catat(db, UID, 'pembayaran_masuk')
db.commit()
cek('pembayaran_masuk tercatat', bool(ok))
np = db.execute(select(Notifikasi).where(
    Notifikasi.user_id == UID,
    Notifikasi.jenis == 'pembayaran_masuk')).scalar_one_or_none()
if np:
    print(f'     judul: "{np.judul}"')
    print(f'     isi  : "{np.isi[:95]}"')

# bersihkan
db.execute(delete(Notifikasi).where(Notifikasi.user_id == UID))
db.commit()
db.close()

print(f'\nHASIL: {lulus} LULUS / {gagal} GAGAL')
sys.exit(0 if gagal == 0 else 1)
