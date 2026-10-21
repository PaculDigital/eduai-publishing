"""Operasi FOLDER workspace user (ACC Bos 15Sep26).

Tujuan bisnis: workspace rapi → user betah unggah → storage naik → untung.
Folder juga jadi alasan upgrade tersendiri (jatah dibatasi per paket).

ATURAN KESELAMATAN DATA:
  ⚠ Menghapus folder TIDAK PERNAH menghapus dokumen.
    Dokumen di dalamnya dipindah ke "tanpa folder" (folder_id = NULL).
  ⚠ Ganti nama / warna tidak menyentuh berkas sama sekali.
  ⚠ Semua operasi hanya boleh menyentuh folder MILIK user sendiri.

Skill terkait: cascade-delete-sqlite (audit dua arah).
"""
from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import FOLDER_IKON, FOLDER_WARNA, boleh_beli_addon, jatah_folder
from .models import FileBerkas, Folder, User

log = logging.getLogger('eduai.folder')

NAMA_MAKS = 100


class FolderGagal(Exception):
    """Operasi folder ditolak (dengan pesan yang layak ditampilkan)."""


def bersihkan_nama(nama: str) -> str:
    """Rapikan nama folder — buang spasi berlebih & batasi panjangnya."""
    n = ' '.join((nama or '').split())
    return n[:NAMA_MAKS]


def jumlah_folder(db: Session, user_id: int) -> int:
    return db.scalar(
        select(func.count(Folder.id)).where(Folder.user_id == user_id)
    ) or 0


def sisa_jatah(db: Session, u: User) -> int | None:
    """Sisa jatah folder (paket + AddOn). None = tak terbatas."""
    jatah = jatah_folder(u.paket, u.folder_ekstra)
    if jatah is None:
        return None
    return max(0, jatah - jumlah_folder(db, u.id))


def daftar_folder(db: Session, user_id: int) -> list[Folder]:
    return list(db.scalars(
        select(Folder).where(Folder.user_id == user_id)
        .order_by(Folder.nama.asc())
    ).all())


def ambil(db: Session, user_id: int, folder_id: int) -> Folder:
    """Ambil folder MILIK user. Folder user lain → dianggap tidak ada."""
    f = db.get(Folder, folder_id)
    if not f or f.user_id != user_id:
        raise FolderGagal('Folder tidak ditemukan.')
    return f


def buat(db: Session, u: User, nama: str, warna: str = 'hijau',
         ikon: str = 'folder') -> Folder:
    """Buat folder baru. Jatah per paket DIPERIKSA di sini."""
    nama = bersihkan_nama(nama)
    if not nama:
        raise FolderGagal('Nama folder tidak boleh kosong.')

    jatah = jatah_folder(u.paket, u.folder_ekstra)
    if jatah is not None and jumlah_folder(db, u.id) >= jatah:
        # ── PESAN DIBEDAKAN PER PAKET (ACC Bos 15Sep26) ──────────────────
        # Paket GRATIS tidak boleh beli AddOn (config.PAKET_TANPA_ADDON).
        # Menyuruh mereka "Tambah AddOn" = menyesatkan: tombolnya tak ada.
        # Yang benar untuk gratis: arahkan ke UPGRADE PAKET.
        if not boleh_beli_addon(u.paket):
            raise FolderGagal(
                '%d of %d Folder Anda sudah Tercapai. '
                'Tingkatkan paket untuk menambah Storage dan Folder Anda.'
                % (jumlah_folder(db, u.id), jatah)
            )
        raise FolderGagal(
            '%d of %d Folder Anda sudah Tercapai. '
            'Tambah AddOn Storage & Folder (+10 folder).'
            % (jumlah_folder(db, u.id), jatah)
        )

    ada = db.scalar(
        select(Folder).where(Folder.user_id == u.id,
                             func.lower(Folder.nama) == nama.lower())
    )
    if ada:
        raise FolderGagal('Sudah ada folder bernama "%s".' % nama)

    f = Folder(
        user_id=u.id, nama=nama,
        warna=warna if warna in FOLDER_WARNA else 'hijau',
        ikon=ikon if ikon in FOLDER_IKON else 'folder',
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    log.info('[folder] user=%s buat folder=%s "%s"', u.id, f.id, f.nama)
    return f


def ubah(db: Session, user_id: int, folder_id: int, nama: str | None = None,
         warna: str | None = None, ikon: str | None = None) -> Folder:
    """Ganti nama / warna / ikon folder. TIDAK menyentuh dokumen."""
    f = ambil(db, user_id, folder_id)

    if nama is not None:
        nama = bersihkan_nama(nama)
        if not nama:
            raise FolderGagal('Nama folder tidak boleh kosong.')
        bentrok = db.scalar(
            select(Folder).where(Folder.user_id == user_id,
                                 func.lower(Folder.nama) == nama.lower(),
                                 Folder.id != folder_id)
        )
        if bentrok:
            raise FolderGagal('Sudah ada folder bernama "%s".' % nama)
        f.nama = nama
    if warna is not None and warna in FOLDER_WARNA:
        f.warna = warna
    if ikon is not None and ikon in FOLDER_IKON:
        f.ikon = ikon

    db.commit()
    db.refresh(f)
    return f


def hapus(db: Session, user_id: int, folder_id: int) -> dict:
    """Hapus folder — DOKUMEN DI DALAMNYA TIDAK IKUT TERHAPUS.

    Dokumen dipindah ke "tanpa folder" (folder_id = NULL). Ini keputusan
    yang disengaja: user sering keliru menekan hapus folder dan tidak boleh
    kehilangan naskahnya.
    """
    f = ambil(db, user_id, folder_id)
    berkas = list(db.scalars(
        select(FileBerkas).where(FileBerkas.folder_id == f.id)
    ).all())
    for b in berkas:
        b.folder_id = None
    db.commit()
    nama = f.nama
    db.delete(f)
    db.commit()
    log.info('[folder] user=%s hapus folder=%s "%s" — %d dokumen dipindah '
             'ke tanpa folder', user_id, folder_id, nama, len(berkas))
    return {'nama': nama, 'dokumen_dipindah': len(berkas)}


def pindahkan(db: Session, user_id: int, file_id: int,
              folder_id: int | None) -> FileBerkas:
    """Pindahkan dokumen ke folder (folder_id=None → keluarkan dari folder)."""
    fb = db.get(FileBerkas, file_id)
    if not fb or fb.user_id != user_id:
        raise FolderGagal('Dokumen tidak ditemukan.')
    if folder_id is None:
        fb.folder_id = None
    else:
        f = ambil(db, user_id, folder_id)       # pastikan folder milik user
        fb.folder_id = f.id
    db.commit()
    db.refresh(fb)
    return fb


def pindahkan_banyak(db: Session, user_id: int, file_ids: list[int],
                     folder_id: int | None) -> int:
    """Pindahkan banyak dokumen sekaligus. Kembalikan jumlah yang berhasil."""
    if folder_id is not None:
        ambil(db, user_id, folder_id)
    n = 0
    for fid in file_ids:
        try:
            fb = db.get(FileBerkas, int(fid))
        except (TypeError, ValueError):
            continue
        if not fb or fb.user_id != user_id:
            continue
        fb.folder_id = folder_id
        n += 1
    db.commit()
    return n


def ringkas(db: Session, u: User) -> dict:
    """Ringkasan untuk UI: daftar folder + berkas tanpa folder + jatah."""
    fl = daftar_folder(db, u.id)
    tanpa = list(db.scalars(
        select(FileBerkas).where(FileBerkas.user_id == u.id,
                                 FileBerkas.folder_id.is_(None),
                                 FileBerkas.terhapus_pada.is_(None))
        .order_by(FileBerkas.dibuat.desc())
    ).all())
    return {
        'folder': fl,
        'tanpa_folder': tanpa,
        'jumlah_folder': len(fl),
        'jatah_folder': jatah_folder(u.paket, u.folder_ekstra),
        'sisa_jatah': sisa_jatah(db, u),
    }
