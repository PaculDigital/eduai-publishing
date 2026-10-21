"""GERBANG JATAH (06Okt26) — 2× gratis per 7 hari, lewat itu 1 token.

Uji SUNGGUHAN dengan DB SALINAN (tidak menyentuh produksi).
  X1. Siklus: sebelum pakai → 2 gratis; belum pernah → siklus mulai sekarang
  X2. Pakai 2× gratis → sisa 0, jenis jadi 'token'
  X3. ⭐ Jatah kembali setelah 7 hari (pergeseran waktu diuji NYATA)
  X4. Batas PER USER (user lain tidak terpengaruh)
  X5. Hanya pencarian MANUAL yang dihitung (bukan otomatis/AI)
  X6. Pesan HANGAT (tanpa kata keras) + ada jalan keluar
  X7. Konstanta sesuai putusan Bos (2 / 7 / 1)
  X8. Tidak ada dompet paralel (pakai kuota, bukan tabel saldo baru)
  X9. Tabel pencarian_manual terbuat + kolomnya lengkap
  X10. catat() tidak commit sendiri (disiplin transaksi)

Cara pakai (dalam container): cd /app && python3 _gerbang_jatah.py
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta


def _naive(**kw):
    """Waktu NAIVE (seperti yang dibaca kembali dari SQLite)."""
    return datetime.utcnow() - timedelta(**kw)

sys.path.insert(0, '/app')

lulus = 0
gagal = 0


def cek(nama: str, syarat: bool, bukti: str = '') -> None:
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  LULUS  {nama}')
    else:
        gagal += 1
        print(f'  GAGAL  {nama}  {bukti}')


#  ── Siapkan DB SALINAN + app yang menunjuk ke sana ──
TMP = tempfile.mkdtemp(prefix='uji_jatah_')
DB = os.path.join(TMP, 'uji.db')
shutil.copyfile('/app/data/eduai.db', DB)


def siapkan():
    os.environ['EDUAI_DB'] = DB
    from app import models as M
    #  paksa engine menunjuk salinan (kalau env belum dipakai)
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        eng = create_engine(f'sqlite:///{DB}')
        M.engine = eng
        M.SessionLocal = sessionmaker(bind=eng, expire_on_commit=False)
        M.init_db()
    except Exception as e:                                    # noqa: BLE001
        print('  (catatan) paksa engine:', type(e).__name__, e)
    return M


M = siapkan()
from app import jatah as JT                                  # noqa: E402


def sesi():
    return M.SessionLocal()


def _user(db, email: str = 'uji-jatah@test.local'):
    from app.models import User as U
    u = db.query(U).filter(U.email == email).first()
    if u is None:
        u = U(email=email, nama='Uji Jatah', password_hash='x')
        db.add(u)
        db.commit()
    return u


def _bersih(db, uid):
    from app.models import PencarianManual as PM
    db.query(PM).filter(PM.user_id == uid).delete()
    db.commit()


# ── X1 ──
def x1() -> None:
    db = sesi()
    try:
        u = _user(db, 'uji-jatah-x1@test.local')
        _bersih(db, u.id)
        r = JT.ringkas(db, u.id)
        cek('X1a belum pernah cari → sisa 2', r['sisa'] == 2, f'({r["sisa"]})')
        cek('X1b terpakai 0', r['terpakai'] == 0)
        cek('X1c ada pesan hangat', bool(r['pesan']))
        b = JT.boleh_cari(db, u.id)
        cek('X1d boleh cari & jenis gratis', b['boleh'] and b['jenis'] == 'gratis')
        cek('X1e gratis → token 0', b['token'] == 0)
    finally:
        db.close()


# ── X2 ──
def x2() -> None:
    db = sesi()
    try:
        u = _user(db, 'uji-jatah-x2@test.local')
        _bersih(db, u.id)
        JT.catat(db, u.id, 'harga, promosi', 'gratis'); db.commit()
        cek('X2a setelah 1 gratis → sisa 1', JT.sisa_gratis(db, u.id) == 1)
        JT.catat(db, u.id, 'kualitas produk', 'gratis'); db.commit()
        cek('X2b setelah 2 gratis → sisa 0', JT.sisa_gratis(db, u.id) == 0)
        b = JT.boleh_cari(db, u.id)
        cek('X2c jenis sekarang = token', b['jenis'] == 'token')
        cek('X2d harga = 1 token', b['token'] == 1)
        r = JT.ringkas(db, u.id)
        cek('X2e pesan sebut Token Revisi', 'Token Revisi' in r['pesan'])
    finally:
        db.close()


# ── X3 ⭐ jatah kembali setelah 7 hari (uji pergeseran waktu NYATA) ──
def x3() -> None:
    db = sesi()
    try:
        u = _user(db, 'uji-jatah-x3@test.local')
        _bersih(db, u.id)
        from app.models import PencarianManual as PM
        #  2 gratis dipakai 8 HARI LALU
        for i in range(2):
            db.add(PM(user_id=u.id, kata_kunci=f'lama{i}', jenis='gratis',
                      dibuat=_naive(days=8, minutes=i)))
        db.commit()
        cek('X3a pencarian 8 hari lalu → sisa 2 LAGI (siklus baru)',
            JT.sisa_gratis(db, u.id) == 2,
            f'({JT.sisa_gratis(db, u.id)})')
        #  2 gratis dipakai 3 HARI LALU → masih siklus berjalan
        _bersih(db, u.id)
        for i in range(2):
            db.add(PM(user_id=u.id, kata_kunci=f'baru{i}', jenis='gratis',
                      dibuat=_naive(days=3, minutes=i)))
        db.commit()
        cek('X3b pencarian 3 hari lalu → sisa 0 (masih siklus)',
            JT.sisa_gratis(db, u.id) == 0, f'({JT.sisa_gratis(db, u.id)})')
        #  ⭐ PERBAIKAN UJI (06Okt26): asumsi awal Wulan SALAH. Siklus
        #     berjalan dihitung dari PEMAKAIAN PERTAMA (8 hari lalu) → siklus
        #     saat ini mulai 1 hari lalu, jadi pencarian "3 hari lalu" jatuh
        #     di siklus SEBELUMNYA dan TIDAK dihitung. Sisa = 2 = BENAR.
        _bersih(db, u.id)
        db.add(PM(user_id=u.id, kata_kunci='a', jenis='gratis',
                  dibuat=_naive(days=8)))
        db.add(PM(user_id=u.id, kata_kunci='b', jenis='gratis',
                  dibuat=_naive(days=3)))
        db.commit()
        cek('X3c 1 lama + 1 baru (siklus berputar) → sisa 2',
            JT.sisa_gratis(db, u.id) == 2, f'({JT.sisa_gratis(db, u.id)})')
        #  Skenario yang benar-benar "masih siklus": dua-duanya DALAM 7 hari
        #  sejak pemakaian pertama.
        _bersih(db, u.id)
        db.add(PM(user_id=u.id, kata_kunci='p', jenis='gratis',
                  dibuat=_naive(days=2, minutes=0)))
        db.add(PM(user_id=u.id, kata_kunci='q', jenis='gratis',
                  dibuat=_naive(days=1)))
        db.commit()
        cek('X3c2 dua-duanya dalam 7 hari pertama → sisa 0',
            JT.sisa_gratis(db, u.id) == 0, f'({JT.sisa_gratis(db, u.id)})')
        #  reset di masa depan
        cek('X3d kapan_reset di MASA DEPAN',
            JT.kapan_reset(db, u.id) > datetime.utcnow())
    finally:
        db.close()


# ── X4 batas per USER ──
def x4() -> None:
    db = sesi()
    try:
        u1 = _user(db, 'uji-jatah-x4a@test.local')
        u2 = _user(db, 'uji-jatah-x4b@test.local')
        _bersih(db, u1.id); _bersih(db, u2.id)
        for i in range(2):
            JT.catat(db, u1.id, f'kk{i}', 'gratis')
        db.commit()
        cek('X4a user1 habis (0)', JT.sisa_gratis(db, u1.id) == 0)
        cek('X4b user2 TIDAK terpengaruh (masih 2)',
            JT.sisa_gratis(db, u2.id) == 2, f'({JT.sisa_gratis(db, u2.id)})')
        cek('X4c user2 masih gratis',
            JT.boleh_cari(db, u2.id)['jenis'] == 'gratis')
    finally:
        db.close()


# ── X5 hanya manual yang dihitung ──
def x5() -> None:
    db = sesi()
    try:
        u = _user(db, 'uji-jatah-x5@test.local')
        _bersih(db, u.id)
        from app.models import PencarianManual as PM
        #  banyak pencarian BERTANDA 'token' + 'ai' (bukan gratis) 8 hari lalu
        for i in range(5):
            db.add(PM(user_id=u.id, kata_kunci=f't{i}', jenis='token', token=1,
                      dibuat=_naive(days=1, minutes=i)))
        db.add(PM(user_id=u.id, kata_kunci='ai1', jenis='ai',
                  dibuat=_naive(days=1)))
        db.commit()
        cek('X5a pencarian TOKEN tidak memakan jatah gratis',
            JT.sisa_gratis(db, u.id) == 2, f'({JT.sisa_gratis(db, u.id)})')
    finally:
        db.close()


# ── X6 pesan hangat ──
def x6() -> None:
    db = sesi()
    try:
        u = _user(db, 'uji-jatah-x6@test.local')
        _bersih(db, u.id)
        r1 = JT.ringkas(db, u.id)
        for i in range(2):
            JT.catat(db, u.id, f'k{i}', 'gratis')
        db.commit()
        r2 = JT.ringkas(db, u.id)
        keras = ('GAGAL', 'PERINGATAN', 'HABIS', 'BAHAYA', 'SEGERA', '!')
        cek('X6a pesan (ada jatah) tanpa kata keras',
            not any(k in r1['pesan'] for k in keras), f'({r1["pesan"]})')
        cek('X6b pesan (habis) tanpa kata keras',
            not any(k in r2['pesan'] for k in keras), f'({r2["pesan"]})')
        cek('X6c pesan habis memberi JALAN KELUAR',
            'kembali' in r2['pesan'] or 'Token Revisi' in r2['pesan'])
        p = JT.pesan_tidak_cukup_saldo()
        cek('X6d pesan saldo kurang tanpa kata keras',
            not any(k in p for k in keras), f'({p})')
        cek('X6e pesan saldo kurang menawarkan cara',
            'isi token' in p or 'tunggu' in p)
    finally:
        db.close()


# ── X7 konstanta ──
def x7() -> None:
    cek('X7a jatah gratis = 2 (putusan Bos)', JT.JATAH_GRATIS == 2)
    cek('X7b siklus = 7 hari (putusan Bos)', JT.SIKLUS_HARI == 7)
    cek('X7c harga = 1 token (putusan Bos)', JT.HARGA_TOKEN == 1)


# ── X8 tidak ada dompet paralel ──
def x8() -> None:
    from pathlib import Path
    isi = Path('/app/app/jatah.py').read_text(encoding='utf-8')
    cek('X8a jatah.py TIDAK membuat tabel saldo sendiri',
        'class Saldo' not in isi and 'saldo_token' not in isi)
    cek('X8b jatah.py menyebut kuota (satu pintu dompet)',
        'kuota' in isi.lower())
    m = Path('/app/app/models.py').read_text(encoding='utf-8')
    cek('X8c models.py TIDAK menambah tabel dompet baru',
        m.count('class SaldoToken') == 1)


# ── X9 tabel & kolom ──
def x9() -> None:
    import sqlite3
    c = sqlite3.connect(DB)
    tabs = [r[0] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")]
    cek('X9a tabel pencarian_manual TERBUAT', 'pencarian_manual' in tabs)
    kol = [r[1] for r in c.execute('PRAGMA table_info(pencarian_manual)')]
    for k in ('id', 'user_id', 'file_id', 'bab', 'kata_kunci', 'jenis',
              'token', 'hasil_jumlah', 'dibuat'):
        cek(f'X9b kolom {k} ada', k in kol)
    cek('X9c jumlah kolom = 9', len(kol) == 9, f'({kol})')


# ── X10 disiplin transaksi ──
def x10() -> None:
    db = sesi()
    try:
        u = _user(db, 'uji-jatah-x10@test.local')
        _bersih(db, u.id)
        JT.catat(db, u.id, 'belum-commit', 'gratis')
        db.rollback()                       # batalkan
        from app.models import PencarianManual as PM
        n = db.query(PM).filter(PM.user_id == u.id).count()
        cek('X10a catat() TIDAK commit sendiri (rollback bisa membatalkan)',
            n == 0, f'({n} baris tersisa)')
    finally:
        db.close()


def main() -> int:
    print('=== GERBANG JATAH — 2× gratis / 7 hari, lewat itu 1 token ===')
    for fn in (x1, x2, x3, x4, x5, x6, x7, x8, x9, x10):
        try:
            fn()
        except Exception as e:                                # noqa: BLE001
            cek(f'{fn.__name__} tidak melempar', False,
                f'({type(e).__name__}: {e})')
    print(f'\nTOTAL: {lulus} LULUS / {gagal} GAGAL')
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
