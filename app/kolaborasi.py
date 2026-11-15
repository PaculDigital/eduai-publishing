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

from fastapi import APIRouter, Depends, Form, Request
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
                             db: Session = Depends(get_db),
                             perintah: str | None = Form(None),
                             pilih: str = Form(''),
                             berkas_id: str = Form('')):
    """Tombol 'Asisten Ai (1 Token)' — AI baca naskah, usulan LANGSUNG
    masuk (C5).

    DUA MODE (15 Nov 2026, alur pilihan di sidebar):
      · `perintah` TIDAK dikirim (halaman Kolaborasi) atau perintah SEMPIT
        → alur lama: 1 token per operasi, usulan langsung jadi catatan.
      · `perintah` kosong/luas → alur pilihan: pembuatan daftar GRATIS,
        AI memberi 5 pilihan per round (disimpan, bukan catatan).
      · `pilih` terisi ("0,2") → TERIMA pilihan: 1 Token Revisi per butir
        (trial menanggung butir pertama), tanpa panggilan AI baru.

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
    if (pilih or '').strip():
        #  Terima pilihan: tanpa AI baru, 1 token per butir yang dipilih.
        return _asisten.terima_pilihan(db, b, u, berkas_id, pilih)
    hasil = await _asisten.kerjakan(db, b, u,
                                    perintah=perintah)  # C7: pembayar = yang klik
    return hasil


@router.post('/kolaborasi/balasan')
def kolaborasi_balasan(
    bimbingan_id: int = Form(0),
    induk_id: int = Form(0),
    isi: str = Form(''),
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    """Mahasiswa membalas satu rantai catatan (15 Nov 2026, GAS Bos 21:56 WIB).

    Balasan menempel ke catatan TERBARU rantai (induk_id) dan mewarisi
    alamat bagian + berkas dari catatan itu — mahasiswa tidak memilih
    alamat sendiri (sama seperti balasan pembimbing di jalur token).
    Penulis ditandai mahasiswa (dari_pembimbing=False, warna biru).
    Catatan TIDAK kena kuota. Sesudah tersimpan, pembimbing dikabari
    lewat WA (best-effort, saklar per-tautan) — gagal kirim tidak
    menggagalkan balasan.

    Keamanan: bimbingan WAJIB milik akun ini (pemilik naskah saja —
    pembimbing berakun membalas lewat jalur token, bukan di sini);
    induk WAJIB catatan di bimbingan itu.
    """
    from . import pembimbing as P
    from .models import BerkasPembimbingan, CatatanPembimbing, FileBerkas
    b = db.get(Pembimbingan, bimbingan_id) if bimbingan_id else None
    if b is None or b.user_id != u.id or b.dicabut:
        return RedirectResponse('/naskah', status_code=303)
    induk = db.get(CatatanPembimbing, induk_id) if induk_id else None
    if induk is None or induk.pembimbingan_id != b.id:
        return RedirectResponse('/naskah', status_code=303)
    if not (isi or '').strip():
        return _kembali_editor(db, b, induk)
    #  ── KUNCI SELESAI (16 Nov 2026, sidebar sederhana, GAS Bos 00:42 WIB)
    #  Balasan ke rantai yang sudah diakhiri pembimbing DITOLAK (tidak
    #  disimpan): kartu itu sudah jadi riwayat baca saja. Rantai yang
    #  selesai OTOMATIS (sudah_oke) TIDAK tertutup oleh ini.
    if P.rantai_tertutup(db, b.id, induk.id):
        log.warning('[kolaborasi] balasan ke rantai tertutup ditolak: %s',
                    induk.id)
        return _kembali_editor(db, b, induk)
    P.catat(db, b, isi,
            section_id=induk.section_id or '',
            section_judul=induk.section_judul or '',
            dari_pembimbing=False, induk_id=induk.id,
            berkas_id=induk.berkas_id)
    try:
        _fid = None
        _judul = 'Naskah'
        if induk.berkas_id is not None:
            _bk = db.get(BerkasPembimbingan, induk.berkas_id)
            if _bk is not None:
                _fid = _bk.file_id
        if _fid is None:
            _semua = P.daftar_berkas(db, b.id)
            if _semua:
                _fid = _semua[0].file_id
        if _fid is not None:
            _fb = db.get(FileBerkas, _fid)
            if _fb is not None and (_fb.nama or '').strip():
                _judul = _fb.nama
        P.beri_tahu_balasan_pembimbing(db, b, _judul)
    except Exception as e:                                     # noqa: BLE001
        log.warning('[kolaborasi] WA balasan ke pembimbing gagal: %s', e)
    return _kembali_editor(db, b, induk)


def _kembali_editor(db: Session, b: Pembimbingan, induk):
    """Kembali ke editor naskah rantai itu, atau /naskah bila tak ada."""
    from . import pembimbing as P
    from .models import BerkasPembimbingan
    fid = None
    if induk is not None and getattr(induk, 'berkas_id', None) is not None:
        bk = db.get(BerkasPembimbingan, induk.berkas_id)
        if bk is not None:
            fid = bk.file_id
    if fid is None:
        semua = P.daftar_berkas(db, b.id)
        if semua:
            fid = semua[0].file_id
    if fid:
        return RedirectResponse(f'/edit/{fid}', status_code=303)
    return RedirectResponse('/naskah', status_code=303)


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
