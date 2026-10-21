"""Tong Sampah berkas — seperti Google Drive (ACC Bos 14Sep26).

═══════════════════════════════════════════════════════════════════════════
ALUR (ACC Bos):
  [User klik hapus] → [KONFIRMASI] → [masuk TONG SAMPAH] → (30 hari)
                                                          → hapus permanen

ATURAN yang disetujui Bos:
  • lama simpan ....... 30 hari (SAMPAH_HARI)
  • kuota ............. TETAP dihitung selagi di sampah (adil)
  • siapa lihat ....... hanya pemilik berkas
  • backup ............ DB di-backup otomatis SEBELUM hapus permanen
  • auto-bersih ....... lazy (dicek saat halaman sampah dibuka)
═══════════════════════════════════════════════════════════════════════════

KENAPA LAZY, bukan cron: project ini belum punya cron. Auto-bersih dijalankan
setiap kali user membuka halaman Tong Sampah (dan saat hapus permanen manual),
jadi tidak perlu scheduler baru.
"""

from __future__ import annotations

import logging
import shutil
import sqlite3
from datetime import timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .cascade import HapusGagal, hapus_berkas
from .config import SAMPAH_BACKUP_DIR, SAMPAH_BACKUP_SIMPAN, SAMPAH_HARI
from .models import FileBerkas, User, _now

log = logging.getLogger('eduai.sampah')


# ═══════════════════════════════════════════════════════════════════════
#  PINDAH KE SAMPAH / PULIHKAN  (kebalikan satu sama lain)
# ═══════════════════════════════════════════════════════════════════════

def ke_sampah(db: Session, fb: FileBerkas) -> FileBerkas:
    """Pindahkan berkas ke Tong Sampah. File di disk TIDAK disentuh.

    Kuota TETAP dihitung (Bos: "tetap makan kuota"), jadi `terpakai_mb`
    user tidak berubah — berkas masih ada, cuma disembunyikan.
    """
    fb.terhapus_pada = _now()
    db.commit()
    db.refresh(fb)
    log.info('[sampah] berkas id=%s masuk sampah (sisa %d hari)', fb.id, SAMPAH_HARI)
    return fb


def pulihkan(db: Session, fb: FileBerkas) -> FileBerkas:
    """Kembalikan berkas dari Tong Sampah ke daftar dokumen."""
    fb.terhapus_pada = None
    db.commit()
    db.refresh(fb)
    log.info('[sampah] berkas id=%s dipulihkan', fb.id)
    return fb


def daftar_sampah(db: Session, user_id: int) -> list[FileBerkas]:
    """Berkas milik user yang sedang di Tong Sampah (terbaru dulu)."""
    return list(db.scalars(
        select(FileBerkas)
        .where(FileBerkas.user_id == user_id,
               FileBerkas.terhapus_pada.is_not(None))
        .order_by(FileBerkas.terhapus_pada.desc())
    ).all())


def daftar_aktif(db: Session, user_id: int) -> list[FileBerkas]:
    """Berkas milik user yang AKTIF (tidak di sampah) — terbaru dulu."""
    return list(db.scalars(
        select(FileBerkas)
        .where(FileBerkas.user_id == user_id,
               FileBerkas.terhapus_pada.is_(None))
        .order_by(FileBerkas.dibuat.desc())
    ).all())


def ukuran_sampah_mb(db: Session, user_id: int) -> float:
    """Berapa MB yang ditahan Tong Sampah (tetap dihitung sebagai terpakai)."""
    total = sum(fb.ukuran or 0 for fb in daftar_sampah(db, user_id))
    return round(total / (1024 * 1024), 2)


# ═══════════════════════════════════════════════════════════════════════
#  HAPUS PERMANEN  (dengan backup otomatis)
# ═══════════════════════════════════════════════════════════════════════

def backup_db(alasan: str = 'sampah') -> str | None:
    """Backup DB sebelum tindakan destruktif. Simpan maksimal N backup.

    KENAPA: Bos minta "kalau hapus otomatis terbackup" — supaya kesalahan
    hapus masih bisa diselamatkan. Gagal backup TIDAK membatalkan hapus
    (biar tidak macet), tapi dicatat di log sebagai peringatan.
    """
    from .config import DB_PATH
    try:
        sumber = Path(DB_PATH)
        if not sumber.exists():
            log.warning('[sampah] DB %s tidak ada — backup dilewati', sumber)
            return None
        # checkpoint WAL dulu supaya backup berisi data terbaru
        try:
            c = sqlite3.connect(str(sumber))
            c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            c.close()
        except sqlite3.Error as e:                        # pragma: no cover
            log.warning('[sampah] checkpoint gagal: %s', e)

        tujuan_dir = Path(SAMPAH_BACKUP_DIR)
        tujuan_dir.mkdir(parents=True, exist_ok=True)
        nama = f'eduai-{_now().strftime("%Y%m%d-%H%M%S")}-{alasan}.db'
        tujuan = tujuan_dir / nama
        shutil.copy2(sumber, tujuan)

        # simpan maksimal SAMPAH_BACKUP_SIMPAN backup terbaru
        semua = sorted(tujuan_dir.glob('eduai-*.db'),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        for tua in semua[SAMPAH_BACKUP_SIMPAN:]:
            try:
                tua.unlink()
            except OSError:                               # pragma: no cover
                pass
        log.info('[sampah] backup DB: %s', tujuan.name)
        return str(tujuan)
    except Exception as e:                                # pragma: no cover
        log.warning('[sampah] backup DB GAGAL (hapus tetap lanjut): %s', e)
        return None


def hapus_permanen(db: Session, fb: FileBerkas, *, alasan: str = 'manual') -> dict:
    """Hapus berkas dari sampah secara PERMANEN (file disk + baris DB + versi).

    Backup DB otomatis dijalankan lebih dulu.
    """
    b = backup_db(f'alasan-{alasan}')
    hasil = hapus_berkas(db, fb)          # cascade: versi, sesi, belajar ikut
    hasil['backup'] = b
    hasil['alasan'] = alasan
    log.info('[sampah] HAPUS PERMANEN berkas id=%s (%s)', fb.id, alasan)
    return hasil


# ═══════════════════════════════════════════════════════════════════════
#  AUTO-BERSIH (lazy): berkas di sampah > SAMPAH_HARI hari
# ═══════════════════════════════════════════════════════════════════════

def bersihkan_kedaluwarsa(db: Session, user_id: int | None = None) -> dict:
    """Hapus permanen berkas sampah yang sudah lewat SAMPAH_HARI hari.

    Dipanggil LAZY (saat halaman sampah dibuka / saat hapus manual).
    `user_id=None` = bersihkan semua user (dipakai admin/uji).
    Aman dipanggil berkali-kali.
    """
    batas = _now() - timedelta(days=SAMPAH_HARI)
    q = select(FileBerkas).where(
        FileBerkas.terhapus_pada.is_not(None),
        FileBerkas.terhapus_pada <= batas,
    )
    if user_id is not None:
        q = q.where(FileBerkas.user_id == user_id)
    kadaluwarsa = list(db.scalars(q).all())

    if not kadaluwarsa:
        return {'jumlah': 0, 'berkas': [], 'backup': None}

    backup = backup_db('auto-bersih')
    berhasil, gagal = [], []
    for fb in kadaluwarsa:
        fid = fb.id
        try:
            hapus_berkas(db, fb)
            berhasil.append(fid)
        except HapusGagal as e:
            # JANGAN gagal diam-diam: dicatat, dan berkas DIBIARKAN di sampah
            # (lebih baik tetap ada daripada setengah terhapus/yatim).
            db.rollback()
            gagal.append({'file_id': fid, 'sebab': str(e)[:120]})
            log.error('[sampah] auto-bersih gagal id=%s: %s', fid, e)
    log.info('[sampah] auto-bersih: %d dihapus, %d gagal', len(berhasil), len(gagal))
    return {'jumlah': len(berhasil), 'berkas': berhasil,
            'gagal': gagal, 'backup': backup}
