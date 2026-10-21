"""Manajemen sesi edit OnlyOffice (batas N dokumen bersamaan per user).

KENAPA DIPERLUKAN (permintaan Bos 12Sep26):
  Setiap dokumen yang dibuka OnlyOffice menahan:
    - 1 proses editor (docservice/converter)
    - cache .bin dokumen tersebut di memori/disk server
    - 1 koneksi WebSocket yang terus hidup

  Kalau 1 user bebas membuka 5 dokumen sekaligus, beban VPS naik 5x.
  Apalagi kalau banyak user. Karenya dibatasi MAX_SESI_EDIT (default 3).

ATURAN PENTING (biar tidak ada kerja user yang hilang):
  1. Sesi BASI (tidak ada heartbeat > SESI_IDLE_MENIT) dibersihkan dulu,
     supaya tab yang ditutup paksa / koneksi putus tidak "menahan" kuota.
  2. Membuka ULANG berkas yang SAMA tidak dihitung sesi baru — kalau tidak,
     user yang me-refresh halaman akan langsung kehabisan kuota.
  3. Sebelum menutup paksa SELALU forcesave dulu. Kalau forcesave GAGAL,
     penutupan DIBATALKAN — lebih baik user diminta simpan manual daripada
     kehilangan hasil kerja.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import MAX_SESI_EDIT, SESI_IDLE_MENIT
from .models import FileBerkas, SesiEdit

log = logging.getLogger('eduai.sesi')


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sadar(dt: datetime | None) -> datetime:
    """Pastikan datetime punya tz-info (UTC) sebelum dihitung selisihnya.

    KENAPA: SQLite menyimpan DateTime TANPA zona waktu. Walaupun kolom
    dideklarasikan DateTime(timezone=True), driver sqlite3 tetap bisa
    mengembalikan nilai NAIVE. Kalau nilai naive dikurangi dengan
    datetime.now(timezone.utc), Python melempar:
        TypeError: can't subtract offset-naive and offset-aware datetimes
    Jadi setiap nilai dari DB dilewatkan fungsi ini dulu.
    """
    if dt is None:
        return _now()
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _umur_menit(dt: datetime | None) -> int:
    """Umur dalam menit sejak dt sampai sekarang (aman naive/aware)."""
    return int((_now() - _sadar(dt)).total_seconds() // 60)


def bersihkan_basi(db: Session, user_id: int | None = None) -> int:
    """Hapus sesi yang tidak ada heartbeat > SESI_IDLE_MENIT.

    Returns: jumlah sesi yang dibersihkan.

    Catatan: TIDAK melakukan forcesave — sesi basi artinya editor sudah
    tidak terhubung, jadi perintah forcesave tidak akan sampai. OnlyOffice
    sendiri sudah menutup dokumen bila tidak ada klien (autosave jalan
    sebelum proses dilepas).
    """
    batas = _now() - timedelta(minutes=SESI_IDLE_MENIT)
    basi = [s for s in db.scalars(select(SesiEdit)).all()
            if _sadar(s.terakhir_aktif) < batas
            and (user_id is None or s.user_id == user_id)]
    for s in basi:
        log.info('[sesi] basi dibersihkan: user=%s file=%s (idle > %s menit)',
                 s.user_id, s.file_id, SESI_IDLE_MENIT)
        db.delete(s)
    if basi:
        db.commit()
    return len(basi)


def sesi_user(db: Session, user_id: int) -> list[SesiEdit]:
    """Sesi AKTIF milik user (setelah membersihkan yang basi)."""
    bersihkan_basi(db, user_id)
    return list(db.scalars(
        select(SesiEdit).where(SesiEdit.user_id == user_id)
        .order_by(SesiEdit.dibuka.desc())).all())


def cek_izin_buka(db: Session, user_id: int, file_id: int) -> dict:
    """Boleh membuka berkas ini di editor?

    Returns:
        {'boleh': bool, 'alasan': str, 'sesi_aktif': int, 'batas': int,
         'sudah_terbuka': bool, 'sesi': [nama berkas...]}
    """
    aktif = sesi_user(db, user_id)

    # Aturan 2: berkas SAMA yang sudah terbuka -> izinkan (refresh, bukan sesi baru)
    for s in aktif:
        if s.file_id == file_id:
            return {'boleh': True, 'alasan': 'berkas ini sudah terbuka',
                    'sesi_aktif': len(aktif), 'batas': MAX_SESI_EDIT,
                    'sudah_terbuka': True, 'sesi': []}

    if len(aktif) >= MAX_SESI_EDIT:
        daftar = []
        for s in aktif:
            fb = db.get(FileBerkas, s.file_id)
            daftar.append({
                'file_id': s.file_id,
                'nama': fb.nama if fb else '(hilang)',
                'menit': _umur_menit(s.terakhir_aktif),
            })
        return {'boleh': False,
                'alasan': (f'Batas {MAX_SESI_EDIT} dokumen bersamaan tercapai. '
                           'Simpan & tutup salah satu dokumen dulu.'),
                'sesi_aktif': len(aktif), 'batas': MAX_SESI_EDIT,
                'sudah_terbuka': False, 'sesi': daftar}

    return {'boleh': True, 'alasan': '', 'sesi_aktif': len(aktif),
            'batas': MAX_SESI_EDIT, 'sudah_terbuka': False, 'sesi': []}


def buka_sesi(db: Session, user_id: int, file_id: int, kunci_oo: str) -> SesiEdit:
    """Catat bahwa user membuka berkas ini di editor."""
    s = db.scalar(select(SesiEdit).where(SesiEdit.user_id == user_id,
                                         SesiEdit.file_id == file_id))
    if s:
        s.terakhir_aktif = _now()
        s.kunci_oo = kunci_oo or s.kunci_oo
    else:
        s = SesiEdit(user_id=user_id, file_id=file_id, kunci_oo=kunci_oo,
                     dibuka=_now(), terakhir_aktif=_now())
        db.add(s)
    db.commit()
    log.info('[sesi] dibuka: user=%s file=%s', user_id, file_id)
    return s


def heartbeat(db: Session, user_id: int, file_id: int) -> bool:
    """Perbarui terakhir_aktif. False kalau sesi sudah tidak ada."""
    s = db.scalar(select(SesiEdit).where(SesiEdit.user_id == user_id,
                                         SesiEdit.file_id == file_id))
    if not s:
        return False
    s.terakhir_aktif = _now()
    db.commit()
    return True


def tutup_sesi(db: Session, user_id: int, file_id: int) -> dict:
    """Tutup sesi SATU berkas. TIDAK forcesave (lihat tutup_dengan_simpan)."""
    s = db.scalar(select(SesiEdit).where(SesiEdit.user_id == user_id,
                                         SesiEdit.file_id == file_id))
    if not s:
        return {'ok': False, 'pesan': 'sesi tidak ditemukan'}
    db.delete(s)
    db.commit()
    log.info('[sesi] ditutup: user=%s file=%s', user_id, file_id)
    return {'ok': True, 'pesan': 'sesi ditutup'}


def daftar_sesi_ringkas(db, user_id: int) -> list[dict]:
    """Untuk ditampilkan di UI: daftar dokumen yang sedang terbuka."""
    hasil = []
    for s in sesi_user(db, user_id):
        fb = db.get(FileBerkas, s.file_id)
        hasil.append({
            'file_id': s.file_id,
            'nama': fb.nama if fb else '(hilang)',
            'menit': _umur_menit(s.terakhir_aktif),
        })
    return hasil
