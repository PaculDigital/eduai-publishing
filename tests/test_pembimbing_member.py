#!/usr/bin/env python3
"""Uji penyelarasan pembimbing-jadi-member + dompet sendiri (15 Nov 2026).

Jalankan `python3 tests/test_pembimbing_member.py`, keluar 0 bila semua lulus.
Memakai model asli + modul asli di DB sqlite sementara (EDUAI_DATA_DIR),
DB produksi tidak tersentuh. Tidak ada panggilan AI sungguhan: pemanggil
model dimatikan lewat monkeypatch di uji yang memerlukannya.

Aturan yang diuji (perintah Boss 15 Nov 2026 13:18 WIB):
  1. Pembimbing boleh daftar jadi member biasa (POST /daftar terbuka).
  2. Jembatan /kolaborasi/kaitkan tidak menimpa identitas orang lain.
  3. Dompet milik sendiri: potongan memakai saldo si pemakai, bukan mahasiswa.
  4. Pembimbing tidak pernah memakai dompet mahasiswa / AI menolak bukan-pemilik.
  5. Asisten Pembimbing: 1 Token Revisi dari dompet PEMBIMBING (atau trial
     1x seumur akun); saldo kurang -> jalan keluar yang benar-benar bisa
     dipakai; AI gagal -> biaya kembali penuh (termasuk trial).

Perbaikan yang diuji di sini (branch agen/wulan/selaraskan-pembimbing-member):
  F1. Trial kembali saat AI gagal (dulu hangus) + pesan gagal jujur per sumber.
  F2. Pesan saldo kurang Asisten bercabang: AddOn bila bisa, upgrade bila gratis.
  F3. periksa() membedakan 402 (isi ulang/AddOn) dan 403 (upgrade Penulis).
  F4. Formulir identitas di tinjau.html mengarahkan email akun EduAi.
  F5. Biaya Asisten tampil di /kolaborasi SEBELUM klik (trial / 1 token).
"""
import asyncio
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_pembimbing_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
# Kunci palsu untuk uji saja (DB sementara, bukan produksi).
os.environ.setdefault('EDUAI_SECRET_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_ROUTER_KEY', 'uji-sementara-bukan-rahasia')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, '/tmp/j2check')  # sqlalchemy (di venv app sudah ada)

LULUS = []
GAGAL = []


def cek(nama, benar):
    (LULUS if benar else GAGAL).append(nama)
    print(('  LULUS  ' if benar else '  GAGAL  ') + nama)


def buat_user(db, email, paket='gratis'):
    from app.models import User
    u = User(email=email, password_hash='x', nama=email.split('@')[0],
             paket=paket)
    db.add(u)
    db.commit()
    return u


def buat_naskah(db, pemilik, isi):
    """Berkas + versi naskah 300+ karakter + bimbingan + berkas bimbingan."""
    from app.models import (BerkasPembimbingan, FileBerkas, Pembimbingan,
                            VersiDokumen)
    from app import pembimbing as P
    fb = FileBerkas(user_id=pemilik.id, nama='SKRIPSI.docx',
                    nama_simpan='skripsi.docx', ukuran=1000)
    db.add(fb)
    db.commit()
    db.add(VersiDokumen(user_id=pemilik.id, file_id=fb.id, bab='1',
                        isi=isi))
    db.commit()
    token = P.buat_token()
    b = Pembimbingan(user_id=pemilik.id, nama='Prof. Budi',
                     token_sidik=P.sidik_token(token),
                     kedaluwarsa=datetime.now() + timedelta(days=7))
    db.add(b)
    db.commit()
    bk = BerkasPembimbingan(pembimbingan_id=b.id, file_id=fb.id,
                            judul='BAB I')
    db.add(bk)
    db.commit()
    return fb, b, bk, token


def main():
    from app import asisten as A
    from app import kolaborasi as K
    from app import pembimbing as P
    from app import saldo as S
    from app.models import SessionLocal, User, init_db

    init_db()
    db = SessionLocal()
    mhs = buat_user(db, 'mahasiswa@contoh.id')
    sup = buat_user(db, 'pembimbing@contoh.id')
    orang_lain = buat_user(db, 'lain@contoh.id')

    # ── Aturan 2: kaitkan tidak menimpa identitas orang lain ─────────────
    fb, b, bk, token = buat_naskah(db, mhs, 'Kata pendahuluan. ' * 40)
    ok, sebab = K.kaitkan_token(db, token, sup)
    cek('kaitkan identitas kosong -> ok + email tertulis',
        ok and sebab == 'ok' and b.identitas == 'pembimbing@contoh.id')
    ok2, sebab2 = K.kaitkan_token(db, token, sup)
    cek('kaitkan email sama -> idempoten ok',
        ok2 and sebab2 == 'ok')
    ok3, sebab3 = K.kaitkan_token(db, token, orang_lain)
    cek('kaitkan identitas orang lain -> ditolak identitas_lain',
        (not ok3) and sebab3 == 'identitas_lain'
        and b.identitas == 'pembimbing@contoh.id')
    ok4, _ = K.kaitkan_token(db, 'token-tidak-ada', sup)
    cek('kaitkan token tidak ada -> ditolak', not ok4)

    # ── Aturan 4: _bimbingan_milik menolak orang asing ────────────────────
    cek('_bimbingan_milik orang asing -> None',
        K._bimbingan_milik(db, b.id, orang_lain) is None)
    cek('_bimbingan_milik pembimbing terkait -> bimbingan',
        K._bimbingan_milik(db, b.id, sup) is not None)
    cek('_bimbingan_milik pemilik -> bimbingan',
        K._bimbingan_milik(db, b.id, mhs) is not None)

    # ── Aturan 3+5: potong memakai dompet PEMBIMBING ─────────────────────
    saldo_mhs_awal = S.sisa(db, mhs)
    cek('saldo awal mahasiswa 3 (paket gratis)', saldo_mhs_awal == 3)
    hasil = A.potong_biaya(db, sup)
    cek('potong pertama -> trial gratis, saldo tidak berkurang',
        hasil.get('ok') and hasil.get('sumber') == 'trial'
        and S.sisa(db, sup) == 3)
    S.masuk(db, sup, 2, sumber='uji')
    hasil2 = A.potong_biaya(db, sup)
    cek('potong kedua -> saldo pembimbing (sisa 4)',
        hasil2.get('ok') and hasil2.get('sumber') == 'saldo'
        and hasil2.get('sisa') == 4)
    cek('saldo mahasiswa tidak tersentuh potongan pembimbing',
        S.sisa(db, mhs) == 3)

    # ── F1: trial kembali saat AI gagal + pesan jujur ─────────────────────
    sup2 = buat_user(db, 'pembimbing2@contoh.id')
    cek('trial baru tersedia', A.sisa_trial(db, sup2))
    A.potong_biaya(db, sup2)
    cek('trial terpakai sesudah potong', not A.sisa_trial(db, sup2))
    A.kembalikan_biaya(db, sup2, 'trial')
    cek('F1: trial kembali sesudah kembalikan_biaya(trial)',
        A.sisa_trial(db, sup2))
    hasil_ulangi = A.potong_biaya(db, sup2)
    cek('F1: trial yang kembali bisa dipakai lagi (bukan sekadar bendera)',
        hasil_ulangi.get('ok') and hasil_ulangi.get('sumber') == 'trial'
        and S.sisa(db, sup2) == 3)
    A.kembalikan_biaya(db, sup2, 'trial')  # pulihkan lagi untuk uji kerjakan

    # F1 ujung-ke-ujung: kerjakan gagal (model dimatikan) -> trial pulih +
    # pesan menyebut jatah gratis, bukan saldo.
    from app import ai as AI
    asli_panggil = AI._panggil_router

    async def _gagal(*a, **k):
        raise RuntimeError('uji: model dimatikan')

    AI._panggil_router = _gagal
    try:
        hasil_gagal = asyncio.run(A.kerjakan(db, b, sup2))
    finally:
        AI._panggil_router = asli_panggil
    cek('F1: kerjakan gagal -> ok False + pesan jatah gratis',
        (not hasil_gagal.get('ok'))
        and 'Jatah gratis' in (hasil_gagal.get('pesan') or ''))
    cek('F1: trial masih tersedia sesudah kerjakan gagal',
        A.sisa_trial(db, sup2))
    cek('F1: saldo pembimbing tidak berkurang saat kerjakan gagal',
        S.sisa(db, sup2) == 3)

    # ── F2: pesan saldo kurang bercabang AddOn vs upgrade ────────────────
    sup_gratis = buat_user(db, 'gratis@contoh.id', paket='gratis')
    A._tandai_trial(db, sup_gratis)
    S.pakai(db, sup_gratis, S.sisa(db, sup_gratis))
    cek('saldo gratis dikuras ke 0', S.sisa(db, sup_gratis) == 0)
    pesan_gratis = A.potong_biaya(db, sup_gratis).get('pesan') or ''
    cek('F2: pesan gratis -> upgrade Penulis, bukan AddOn',
        'Penulis' in pesan_gratis and 'AddOn' not in pesan_gratis)
    sup_bayar = buat_user(db, 'bayar@contoh.id', paket='penulis')
    A._tandai_trial(db, sup_bayar)
    S.pakai(db, sup_bayar, S.sisa(db, sup_bayar))
    pesan_bayar = A.potong_biaya(db, sup_bayar).get('pesan') or ''
    cek('F2: pesan berbayar -> AddOn',
        'AddOn' in pesan_bayar)

    # ── F3: cek_dan_potong 402 vs 403 + periksa() membedakannya ──────────
    from app import kuota as KU
    from app import pembimbing_ai as PAI
    from fastapi import HTTPException
    try:
        KU.cek_dan_potong(db, sup_gratis, jenis='revisi')
        kode_gratis = None
    except HTTPException as e:
        kode_gratis = e.status_code
    cek('cek_dan_potong gratis saldo 0 -> 403 BUTUH_UPGRADE',
        kode_gratis == 403)
    try:
        KU.cek_dan_potong(db, sup_bayar, jenis='revisi')
        kode_bayar = None
    except HTTPException as e:
        kode_bayar = e.status_code
    cek('cek_dan_potong berbayar saldo 0 -> 402',
        kode_bayar == 402)

    # ── F3 BARU (koreksi harga Bos 16:36 WIB): pembuatan daftar GRATIS ───
    #  `periksa()` TIDAK LAGI memotong kuota saat membuat daftar (dulu
    #  cek_dan_potong 402/403 di sini). Dua cek lama di bawah diganti:
    #  walau cek_dan_potong dimatikan ke 403/402, periksa() TETAP jalan
    #  (tidak pernah memanggilnya) dan mengembalikan daftar pilihan.
    #  Tagihan baru jatuh saat butir DITERIMA (1 token per butir), itu
    #  diuji di test_tinjau_sidebar.py. cek_dan_potong sendiri tetap
    #  diuji di atas (403 gratis / 402 berbayar), mesinnya tidak berubah.
    sup3 = buat_user(db, 'pembimbing3@contoh.id')
    fb3, b3, bk3, _t3 = buat_naskah(db, mhs, 'Isi bab tiga. ' * 40)
    asli_cek = KU.cek_dan_potong
    asli_panggil3 = AI._panggil_router

    async def _jawab_periksa(*a, **k):
        isi = ('{"catatan": [{"bagian": "BAB I", "kutipan": "Isi bab tiga", '
               '"soal": "Perlu contoh yang lebih jelas.", '
               '"saran": "Tambahkan satu contoh nyata."}]}')
        return isi, {'model': 'uji'}

    def _naik403(*a, **k):
        raise HTTPException(403, detail='uji')

    def _naik402(*a, **k):
        raise HTTPException(402, detail='uji')

    AI._panggil_router = _jawab_periksa
    saldo3_awal = S.sisa(db, sup3)
    for _kode, _naik in (('403', _naik403), ('402', _naik402)):
        KU.cek_dan_potong = _naik
        try:
            r_baru = asyncio.run(
                PAI.periksa(db, bk3, pemakai=sup3, nama_mhs='Asih'))
        finally:
            KU.cek_dan_potong = asli_cek
        cek(f'F3 baru: periksa abaikan cek_dan_potong {_kode} -> mode pilih, '
            '0 catatan, saldo utuh',
            r_baru.get('ok') and r_baru.get('mode') == 'pilih'
            and r_baru.get('jumlah') == 1
            and S.sisa(db, sup3) == saldo3_awal
            and len([c for c in P.daftar_catatan(db, b3.id)]) == 0)
        #  Bersihkan daftar pilihan supaya putaran berikutnya bersih.
        P.hapus_daftar_pilihan(db, b3.id, bk3.id)
    AI._panggil_router = asli_panggil3

    # ── F5: biaya_untuk + wiring layar ───────────────────────────────────
    sup4 = buat_user(db, 'pembimbing4@contoh.id')
    cek('F5: biaya_untuk trial baru -> pakai_trial True',
        A.biaya_untuk(db, sup4).get('pakai_trial') is True)
    A._tandai_trial(db, sup4)
    b4 = A.biaya_untuk(db, sup4)
    cek('F5: biaya_untuk sesudah trial -> butuh 1 token',
        b4.get('pakai_trial') is False and b4.get('butuh') == 1)
    tpl_kolab = (ROOT / 'app' / 'templates' / 'kolaborasi.html').read_text()
    cek('F5: kolaborasi.html menampilkan biaya sebelum klik',
        'biaya_asisten' in tpl_kolab
        and 'Tinjauan AI pertama gratis' in tpl_kolab
        and '1 Token Revisi dari saldomu' in tpl_kolab)
    tpl_tinjau = (ROOT / 'app' / 'templates' / 'tinjau.html').read_text()
    cek('F4: tinjau.html mengarahkan email akun EduAi',
        'email yang sama dengan akun EduAi' in tpl_tinjau)

    # ── Aturan 1: pendaftaran terbuka (rute /daftar ada, tanpa peran) ────
    src_main = (ROOT / 'app' / 'main.py').read_text()
    cek('Aturan 1: POST /daftar membuat role client tanpa pilihan peran',
        "@app.post('/daftar')" in src_main
        and "role='client'" in src_main)

    print(f'\n{len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL: ' + ', '.join(GAGAL))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
