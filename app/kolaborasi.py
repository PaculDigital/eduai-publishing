"""KOLABORASI — TAB 2 dasbor (T5.1 Opsi A, ACC Bos 27Sep26).

Rancangan:
  · Rute /kolaborasi  → daftar naskah yang diundangkan KE saya
    (pencocokan = email akun ↔ pembimbingan.identitas, C1c: akun
    per email; identitas diisi pembimbing sendiri saat buka link).
  · Rute /kolaborasi/kaitkan  → JEMBATAN: pembimbing yang membuka
    link /tinjau/{token} lalu DAFTAR/MASUK → token disimpan sementara
    di query, saat kaitkan kita tulis email akun ke pembimbingan.
    identitas (bila kolom masih kosong) → naskah otomatis muncul di
    /kolaborasi.
  · Jalur lama /tinjau TIDAK disentuh (putusan C8: disembunyikan
    saja, jangan diputus).

ATURAN KEAMANAN (ikut 3 kunci pengaman models.py):
  · HANYA LIHAT — Tab 2 tidak menambah hak edit.
  · Pencocokan email TIDAK peka huruf besar-kecil (email selalu
    lowercase di proses_daftar).
  · Kalau pembimbingan.identitas sudah terisi OLEH ORANG LAIN,
    kaitan DITOLAK — jangan menimpa identitas orang (sama dengan
    aturan catat_dibuka).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import wajib_login
from .models import get_db
from .models import Pembimbingan, User

#  🤖 T5.2 (ACC Bos 27Sep26): Asisten Pembimbing = 1 endpoint POST.
#  Sengaja di FILE INI (bukan rute_pembimbing.py) karena rute ini milik
#  AKUN pembimbing (butuh login), sedangkan rute_pembimbing = jalur token.
from . import asisten as _asisten

log = logging.getLogger('eduai.kolaborasi')

router = APIRouter(tags=['kolaborasi'])


def _tpl(templates, nama: str, **isi):
    return templates.TemplateResponse(nama, isi)


def daftar_untuk(db: Session, u: User) -> list[dict]:
    """Naskah yang diundangkan KE akun ini (email = identitas).

    Return list ringkas per bimbingan: {b, nama_mahasiswa, sisa_hari}.
    Kosong = belum ada yang mengundang — template WAJIB menampilkan
    pesan ramah (jangan jadikan halaman mati).
    """
    from .pembimbing import sisa_hari  # hindari import lingkar
    email = (u.email or '').strip().lower()
    if not email:
        return []
    hasil = []
    for b in db.scalars(
        select(Pembimbingan)
        .where(Pembimbingan.identitas == email,
               Pembimbingan.dicabut == 0)
        .order_by(Pembimbingan.dibuat.desc())
    ).all():
        hasil.append({'b': b, 'sisa_hari': sisa_hari(b)})
    return hasil


def token_tinjau(db: Session, bimbingan_id: int, u: User) -> str | None:
    """URL /tinjau/{token} untuk bimbingan yang mengundang AKUN INI.

    ⚠️ Token mentah TIDAK disimpan DB (hanya sidik) → kita TIDAK BISA
    mengembalikan token asli. Yang bisa: bikin KARTU UNDANGAN baru untuk
    bimbingan yang sama? — TIDAK: itu mengganti link milik mahasiswa.
    Jalan yang JUJUR: kembalikan None dan template menyuruh membuka link
    asli dari pesan mahasiswa; halaman /kolaborasi menampilkan ringkasan
    + tombol ke /tinjau/kaitkan?… Tidak — solusi bersih: simpan pemetaan
    sidik→mentah di tabel? DILARANG (melanggar desain keamanan DB).

    KARENA ITU tombol 'Buka tinjauan' di Tab 2 TIDAK memakai fungsi ini —
    ia memakai /kolaborasi/buka/{id} yang di sana kita VERIFIKASI kepemilikan
    (email cocok) lalu mengarahkan pembimbing membuka KARTU UNDANGAN BARU
    yang dibuat oleh MAHASISWA? — juga salah.

    KEPUTUSAN AKHIR (jujur): tombol 'Buka tinjauan' hanya mungkin kalau
    kita punya token. Solusi yang dipakai: /kolaborasi/buka/{id} mengembalikan
    halaman kecil berisi penjelasan 'buka lewat link dari mahasiswa' bila
    token tak tersimpan. Fungsi ini TIDAK dipakai — dibiarkan None.
    """
    return None


def kaitkan_token(db: Session, token: str, u: User) -> tuple[bool, str]:
    """Tulis email akun ke pembimbingan.identitas (jemaat → akun).

    Sah HANYA bila: token ada & hidup, dan identitas masih kosong
    ATAU sudah sama dengan email akun (idempoten). Kalau terisi oleh
    email lain → tolak (bukan naskahmu).
    """
    from . import pembimbing as P
    b, sebab = P.cari_dari_token(db, token)
    if b is None:
        return False, sebab
    email = (u.email or '').strip().lower()
    lama = (b.identitas or '').strip().lower()
    if lama and lama != email:
        return False, 'identitas_lain'
    if not lama:
        b.identitas = email
        b.diubah = b.diubah  # onupdate menangani
        db.commit()
        log.info('[kolaborasi] kaitkan bimbingan %s → %s', b.id, email)
    return True, 'ok'


def _bimbingan_milik(db: Session, bimbingan_id: int, u: User):
    """Pemilik sahih ATAU pembimbing yang dikaitkan email — bukan orang lain."""
    b = db.get(Pembimbingan, bimbingan_id)
    if b is None or b.dicabut:
        return None
    email = (u.email or '').strip().lower()
    if b.identitas and (b.identitas or '').strip().lower() == email:
        return b
    #  pemilik naskah juga boleh menekan tombol (uji & demo milik sendiri)
    if b.user_id == u.id:
        return b
    return None


@router.post('/kolaborasi/asisten/{bimbingan_id}')
async def kolaborasi_asisten(bimbingan_id: int, request: Request,
                             u: User = Depends(wajib_login),
                             db: Session = Depends(get_db)):
    """Tombol 'Minta AI tinjau naskah' — AI baca naskah, usulan LANGSUNG
    masuk (C5).

    Keamanan: bimbingan WAJIB milik akun ini (pemilik atau pembimbing
    terkait). Biaya (putusan Bos **C7**, 29Sep26): **yang klik = yang
    bayar** → trial 1× gratis milik AKUN INI (`u`), sesudahnya 1 Token
    Revisi dari SALDO INI. 🚨 DULU: `b_pemilik(db, b)` = pembimbing klik,
    mahasiswa yang dipotong (kebalikan putusan C7 — dompet dua orang jadi
    satu, pemilik bisa rugi tanpa pernah menekan tombol).
    Pagar P1 cek dulu → P2 gagal = kembalikan (pola peta/kerjakan).
    Sengaja SINKRON (bukan utas latar): tinjauan satu naskah terpotong
    40rb karakter, jawaban rata < 60 dtk — di bawah batas Cloudflare.
    """
    b = _bimbingan_milik(db, bimbingan_id, u)
    if b is None:
        return {'ok': False, 'pesan': (
            'Kolaborasi ini bukan milik akunmu, jadi penanya tidak bisa '
            'dijalankan. Buka kolaborasi yang tertera di daftarmu ya.')}
    hasil = await _asisten.kerjakan(db, b, u)   # C7: pembayar = yang klik
    return hasil


def b_pemilik(db: Session, b: Pembimbingan) -> User:
    """User PEMILIK naskah.

    ⚠️ TIDAK DIPAKAI untuk menentukan PEMBAYAR sejak putusan **C7**
    (29Sep26: "yang klik AI = yang bayar"). Rute asisten kini memakai `u`
    (akun yang menekan tombol). Fungsi ini disimpan hanya untuk keperluan
    yang memang butuh pemilik (mis. menampilkan nama pemilik) — jangan
    dikembalikan ke jalur biaya.
    """
    pemilik = db.get(User, b.user_id)
    if pemilik is None:
        raise RuntimeError('pemilik bimbingan tidak ditemukan')
    return pemilik
