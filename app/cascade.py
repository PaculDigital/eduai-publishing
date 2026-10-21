"""Hapus berantai (cascade) terpusat — (ACC Bos 14Sep26).

═══════════════════════════════════════════════════════════════════════════
KENAPA MODUL INI ADA
14Sep26 ditemukan 6 berkas "yatim" di produksi: file di tabel `files` yang
pemiliknya sudah tidak ada di tabel `users`. Penyebabnya `scripts/uji_e2e.py`:
  • `shutil.rmtree(..., ignore_errors=True)` → gagal TANPA suara
  • `db.delete(u)` saja → baris di `files` TIDAK ikut terhapus

Modul ini menutup lubang itu dengan ATURAN WAJIB:
  1. Semua penghapusan data user/berkas HARUS lewat sini — jangan `db.delete`
     mentah di tempat lain.
  2. Kalau penghapusan FILE DI DISK gagal → JANGAN lanjut hapus baris DB.
     Lebih baik "tidak terhapus" daripada "yatim" (file ada tanpa pemilik).
  3. Urutan: baris DB dulu (anak → induk), lalu file disk. Kalau disk gagal,
     transaksi DB di-rollback supaya tidak ada yang setengah jalan.
═══════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import logging
import shutil

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .models import (
    BelajarNaskah, FileBerkas, Folder, PembelianAddon, PemakaianAI, ProfilDokumen,
    RevisiHistory, SectionState, SesiEdit, Transaksi, User, VersiDokumen,
)
from .config import UPLOAD_DIR

log = logging.getLogger('eduai.cascade')

# ⚠ SEMUA tabel yang merujuk ke `users` / `files` — WAJIB dihapus dulu.
#   Ditemukan 14Sep26 lewat `PRAGMA foreign_key_list` setelah bug pertama:
#   Wulan semula LUPA `sesi_edit`, `belajar_naskah`, dan `transaksi` sehingga
#   `DELETE FROM files` ditolak FOREIGN KEY. Jangan kurangi daftar ini tanpa
#   memeriksa ulang seluruh skema:
#     files → users | transaksi → users | sesi_edit → files,users
#     pemakaian_ai → users | pembelian_addon → users
#     belajar_naskah → files,users | versi_dokumen → files,users
#     profil_dokumen → files,users  (ditambah 15Sep26, MASTER_PLAN §4.11)
#     section_state → files,users | revisi_history → files,users  (§4.15 #3/#4)
_ANAK_FILE = (VersiDokumen, SesiEdit, BelajarNaskah, ProfilDokumen,
              SectionState, RevisiHistory)
_ANAK_USER = (VersiDokumen, PemakaianAI, PembelianAddon, SesiEdit,
              BelajarNaskah, Transaksi, Folder, ProfilDokumen,
              SectionState, RevisiHistory)


class HapusGagal(RuntimeError):
    """Penghapusan file di disk gagal — DB TIDAK diubah (rollback)."""


# ═══════════════════════════════════════════════════════════════════════
#  HAPUS SATU BERKAS (dari route /hapus/<fid> ATAU internal)
# ═══════════════════════════════════════════════════════════════════════

def hapus_berkas(db: Session, fb: FileBerkas, *, hapus_file: bool = True) -> dict:
    """Hapus satu berkas + SEMUA versi/sesi/belajar-nya. File disk terakhir.

    Kalau `hapus_file=True` dan file di disk GAGAL dihapus → raise HapusGagal
    dan transaksi di-rollback (tidak ada yang terhapus separuh).
    """
    # Anak-anak yang merujuk file_id: versi_dokumen, sesi_edit, belajar_naskah
    n_anak = {}
    for model in _ANAK_FILE:
        n_anak[model.__tablename__] = db.execute(
            delete(model).where(model.file_id == fb.id)
        ).rowcount or 0

    p = UPLOAD_DIR / str(fb.user_id) / fb.nama_simpan
    db.delete(fb)

    if hapus_file and p.exists():
        try:
            p.unlink()
        except OSError as e:                          # disk gagal → batalkan semua
            db.rollback()
            log.error('[cascade] GAGAL hapus file disk: %s (%s)', p, e)
            raise HapusGagal(
                f'Gagal menghapus file di server: {p.name}. '
                'Berkas tidak dihapus supaya tidak jadi data yatim.'
            ) from e

    db.commit()
    log.info('[cascade] hapus berkas id=%s (%s)', fb.id, n_anak)
    return {'file_id': fb.id, 'anak': n_anak,
            'versi_dihapus': n_anak.get('versi_dokumen', 0)}


# ═══════════════════════════════════════════════════════════════════════
#  HAPUS SATU USER + SELURUH JEJAKNYA
# ═══════════════════════════════════════════════════════════════════════

def hapus_user(db: Session, u: User, *, hapus_file: bool = True) -> dict:
    """Hapus user + SEMUA berkas, versi, pemakaian kuota, pembelian AddOn.

    ATURAN: file di disk dihapus DULU & diverifikasi. Kalau gagal → batal
    seluruhnya (raise HapusGagal), supaya tidak lahir berkas yatim baru.

    Mengembalikan ringkasan: berapa berkas/versi/pemakaian/AddOn dihapus.
    """
    # 1) cek dulu SEMUA file ada di mana (sebelum ada yang dihapus)
    berkas = list(db.scalars(
        select(FileBerkas).where(FileBerkas.user_id == u.id)
    ).all())
    gagal = []
    if hapus_file:
        for fb in berkas:
            p = UPLOAD_DIR / str(u.id) / fb.nama_simpan
            if p.exists():
                try:
                    p.unlink()
                except OSError as e:
                    gagal.append(f'{p.name}: {e}')
        if gagal:
            # Batalkan: jangan lanjut hapus user kalau ada file tertinggal
            log.error('[cascade] GAGAL hapus %d file user id=%s', len(gagal), u.id)
            raise HapusGagal(
                'Tidak semua berkas bisa dihapus di server, jadi penghapusan '
                'akun DIBATALKAN supaya tidak meninggalkan data yatim. '
                f'Gagal: {len(gagal)} berkas.'
            )

        # folder user (kalau kosong) — gagal di sini tidak fatal
        folder = UPLOAD_DIR / str(u.id)
        if folder.exists():
            try:
                shutil.rmtree(folder)
            except OSError as e:                      # pragma: no cover
                log.warning('[cascade] folder user %s tidak bisa dihapus: %s', folder, e)

    # 2) baris DB — anak dulu (semua tabel yang merujuk), induk terakhir
    # ⚠ URUTAN PENTING: `files.folder_id` merujuk `folders.id`, jadi FOLDER
    #   tidak boleh dihapus sebelum baris files. 15Sep26: Folder sempat
    #   ditaruh di _ANAK_USER (paling belakang) → files masih menunjuk folder
    #   yang sudah hilang → FOREIGN KEY constraint failed.
    n_anak = {}
    for model in _ANAK_USER:
        if model is Folder:
            continue                       # folder dihapus SETELAH files
        n_anak[model.__tablename__] = db.execute(
            delete(model).where(model.user_id == u.id)
        ).rowcount or 0
    n_file = db.execute(
        delete(FileBerkas).where(FileBerkas.user_id == u.id)
    ).rowcount or 0
    n_anak['folders'] = db.execute(
        delete(Folder).where(Folder.user_id == u.id)
    ).rowcount or 0
    db.delete(u)
    db.commit()
    log.info('[cascade] hapus user id=%s (file=%d %s)', u.id, n_file, n_anak)
    return {
        'user_id': u.id, 'berkas': n_file,
        'versi': n_anak.get('versi_dokumen', 0),
        'pemakaian': n_anak.get('pemakaian_ai', 0),
        'addon': n_anak.get('pembelian_addon', 0),
        'anak': n_anak,
    }


# ═══════════════════════════════════════════════════════════════════════
#  AUDIT: CARI DATA YATIM (laporan saja — TIDAK menghapus apa pun)
# ═══════════════════════════════════════════════════════════════════════

def cari_yatim(db: Session) -> dict:
    """Laporkan data yatim DUA ARAH. TIDAK menghapus apa pun.

    ARAH 1 — baris DB tanpa pemilik:
        file di tabel `files` yang user-nya sudah tidak ada.

    ARAH 2 — file disk tanpa baris DB  (⚠ ditambahkan 14Sep26):
        file di `uploads/<uid>/` yang tidak punya baris di `files`, ATAU
        folder-nya milik user yang sudah tidak ada. Kasus nyata: folder
        `uploads/7/8cf90d725bb4d94a.png` (11Sep26) — user 7 sudah dihapus,
        baris `files`-nya juga hilang, tapi filenya TERTINGGAL di disk.
        Audit satu arah SERING MELEWATKAN kasus ini.
    """
    ids_user = set(db.scalars(select(User.id)).all())
    berkas = list(db.scalars(select(FileBerkas)).all())

    # ── ARAH 1: baris DB tanpa pemilik ──
    yatim_db = [fb for fb in berkas if fb.user_id not in ids_user]
    rincian_db = []
    for fb in yatim_db:
        p = UPLOAD_DIR / str(fb.user_id) / fb.nama_simpan
        rincian_db.append({
            'file_id': fb.id, 'user_id': fb.user_id, 'nama': fb.nama,
            'ukuran_byte': fb.ukuran, 'ada_di_disk': p.exists(),
            'dibuat': fb.dibuat.isoformat() if fb.dibuat else None,
        })

    # ── ARAH 2: file disk tanpa baris DB / folder tanpa user ──
    dikenal = {(fb.user_id, fb.nama_simpan) for fb in berkas}
    yatim_disk = []
    if UPLOAD_DIR.exists():
        for folder in sorted(UPLOAD_DIR.iterdir()):
            if not folder.is_dir() or not folder.name.isdigit():
                continue
            uid = int(folder.name)
            user_hilang = uid not in ids_user
            for p in sorted(folder.iterdir()):
                if not p.is_file():
                    continue
                tanpa_baris = (uid, p.name) not in dikenal
                if user_hilang or tanpa_baris:
                    yatim_disk.append({
                        'user_id': uid, 'nama_simpan': p.name,
                        'ukuran_byte': p.stat().st_size,
                        'sebab': 'user tidak ada' if user_hilang else 'tanpa baris DB',
                    })

    return {
        # nama lama dipertahankan supaya kode lain tidak pecah
        'jumlah_berkas_yatim': len(rincian_db),
        'total_berkas': len(berkas),
        'rincian': rincian_db,
        # hasil tambahan (arah 2)
        'jumlah_yatim_db': len(rincian_db),
        'jumlah_yatim_disk': len(yatim_disk),
        'rincian_yatim_disk': yatim_disk,
        'ada_yatim': bool(rincian_db or yatim_disk),
    }


def audit_cakupan() -> dict:
    """PERIKSA: apakah _ANAK_FILE & _ANAK_USER sudah mencakup SEMUA FK?

    KENAPA ADA: 14Sep26 Wulan lupa `sesi_edit`, `belajar_naskah`, dan
    `transaksi`, sehingga penghapusan ditolak FOREIGN KEY di tengah jalan.
    Fungsi ini membandingkan daftar di kode dengan skema DB NYATA — jadi
    kalau nanti ada tabel baru yang merujuk users/files, langsung ketahuan.

    Mengembalikan {'lengkap': bool, 'kurang_di_kode': [...], ...}
    Catatan: hanya memeriksa FK ke tabel `users` dan `files`.
    """
    from sqlalchemy import inspect as _inspect
    from .models import engine

    insp = _inspect(engine)
    semua_tabel = set(insp.get_table_names())

    def _perlu_untuk(induk: str) -> set:
        """Tabel mana saja yang punya FK ke `induk`."""
        out = set()
        for t in semua_tabel:
            if t == induk:
                continue
            for fk in insp.get_foreign_keys(t):
                if fk.get('referred_table') == induk:
                    out.add(t)
        return out

    perlu_file = _perlu_untuk('files')
    perlu_user = _perlu_untuk('users')
    punya_file = {m.__tablename__ for m in _ANAK_FILE}
    punya_user = {m.__tablename__ for m in _ANAK_USER}

    kurang_file = sorted(perlu_file - punya_file - {'files'})
    kurang_user = sorted(perlu_user - punya_user - {'files'})
    return {
        'lengkap': not kurang_file and not kurang_user,
        'kurang_di_kode_untuk_files': kurang_file,
        'kurang_di_kode_untuk_users': kurang_user,
        'perlu_untuk_files': sorted(perlu_file),
        'perlu_untuk_users': sorted(perlu_user),
    }
