"""Rute MAHASISWA untuk membagikan naskah ke pembimbing (ACC Bos 23Sep26).

═══════════════════════════════════════════════════════════════════════════
INI SISI MAHASISWA — beda dari `rute_pembimbing.py` (sisi pembimbing).
═══════════════════════════════════════════════════════════════════════════
Permintaan Bos verbatim (23Sep26):
  · "Tombol harus jelas dan Agak besar."
  · "Mahasiswa isi Nama dan No wa (nanti akan di sambung ke webhook wa dan email)"
  · "Dapat link, ada tombol copy dan tombol kirim"
  · "Muncul konfirmasi ok atau batal"

ATURAN BESAR
  1. WAJIB login — ini sisi mahasiswa (pakai `wajib_login`).
  2. Token MENTAH hanya keluar SEKALI (saat dibuat). Yang tersimpan di DB
     hanya sidiknya. Karena itu mahasiswa WAJIB menyalin link saat itu.
     ⚠️ Kalau link hilang, satu-satunya jalan = buat link baru.
  3. Jawaban JSON — tampilan mengurusnya di halaman naskah (tanpa muat ulang).
  4. JANGAN pernah percaya data dari JS: nama, wa, hari, berkas_id DIVALIDASI
     di sini lagi (pelajaran EduAi: batas di JS saja = gerbang mustahil).
"""

from __future__ import annotations

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from . import auth
from . import pembimbing as P
from .config import ARSIP_HARI
from .models import FileBerkas, User, get_db

log = logging.getLogger('eduai.pembimbing.bagikan')

router = APIRouter()


def _butuh_login(request: Request, db: Session) -> User | None:
    """Ambil user dari sesi. None kalau belum login.

    ⚠️ Memakai `auth.user_dari_request` yang SUDAH ADA — jangan baca cookie
    sendiri (nama cookie & cara baca punya satu sumber di auth.py).
    """
    return auth.user_dari_request(request, db)


def _batas_nama(nama: str) -> str:
    return (nama or '').strip()[:120]


@router.get('/pembimbing/daftar')
def daftar(request: Request, db: Session = Depends(get_db)):
    """Daftar pembimbing yang pernah dibagikan (untuk panel di halaman naskah).

    ⚠️ TIDAK ada token mentah di sini — sudah tidak tersimpan di DB.
    """
    u = _butuh_login(request, db)
    if not u:
        return JSONResponse({'ok': False, 'pesan': 'Sesi berakhir.'},
                            status_code=401)
    baris = P.daftar_lengkap(db, u.id)
    for b in baris:
        b['dibuat'] = b['dibuat'].strftime('%d %b %Y') if b['dibuat'] else ''
        b['kedaluwarsa'] = (b['kedaluwarsa'].strftime('%d %b %Y')
                            if b['kedaluwarsa'] else '')
        b['dibuka_pada'] = (b['dibuka_pada'].strftime('%d %b %Y %H:%M')
                            if b['dibuka_pada'] else '')
    return JSONResponse({'ok': True, 'daftar': baris})


@router.post('/pembimbing/bagikan')
def bagikan(
    request: Request,
    nama: str = Form(''),
    wa: str = Form(''),
    email: str = Form(''),
    hari: int = Form(30),
    file_id: int = Form(0),
    db: Session = Depends(get_db),
):
    """Buat link tinjau baru untuk seorang pembimbing.

    Return JSON: {ok, token, link, kirim, sisa_hari} — token MENTAH hanya
    di jawaban ini. Setelah ini tidak bisa diambil lagi.
    """
    u = _butuh_login(request, db)
    if not u:
        return JSONResponse({'ok': False, 'pesan': 'Sesi berakhir.'},
                            status_code=401)

    nama = _batas_nama(nama)
    if not nama:
        return JSONResponse({'ok': False,
                             'pesan': 'Nama pembimbing belum diisi.'})
    if not (wa.strip() or email.strip()):
        return JSONResponse({'ok': False,
                             'pesan': 'Nomor WhatsApp atau email belum diisi.'})

    #  Batas masa berlaku dari SATU sumber (P.MASA_BERLAKU) — jangan
    #  percaya angka dari JS.
    if hari not in P.MASA_BERLAKU:
        hari = P.MASA_BERLAKU[-1]

    #  Naskah: pastikan berkas memang milik mahasiswa ini (jangan bocor).
    fid = None
    judul = 'Naskah'
    if file_id:
        f = (db.query(FileBerkas)
             .filter(FileBerkas.id == file_id, FileBerkas.user_id == u.id)
             .one_or_none())
        if not f:
            return JSONResponse({'ok': False,
                                 'pesan': 'Naskah tidak ditemukan.'})
        fid = f.id
        judul = (f.nama or 'Naskah')[:160]

    b, token = P.buat_bimbingan(db, u.id, nama, hari=hari,
                                wa=wa, email=email,
                                file_id=fid, judul=judul)

    link = f'{P.BASE_PUBLIK}/tinjau/{token}'
    kirim = P.tautan_kirim(b, token, nama_mhs=u.nama or '', judul=judul)

    log.info('[bagikan] bimbingan %s dibuat user=%s (nama=%s, %s hari)',
             b.id, u.id, nama, hari)
    return JSONResponse({
        'ok': True,
        'id': b.id,
        'token': token,          # ⚠️ hanya sekali ini
        'link': link,
        'kirim': kirim,
        'nama': b.nama,
        'wa': b.wa,
        'email': b.email,
        'sisa_hari': P.sisa_hari(b),
        'naskah': judul,
    })


@router.post('/pembimbing/cabut')
def cabut(
    request: Request,
    bimbingan_id: int = Form(0),
    db: Session = Depends(get_db),
):
    """Cabut link — mati seketika. Catatan pembimbing TIDAK dihapus."""
    u = _butuh_login(request, db)
    if not u:
        return JSONResponse({'ok': False, 'pesan': 'Sesi berakhir.'},
                            status_code=401)
    if not bimbingan_id:
        return JSONResponse({'ok': False, 'pesan': 'Link tidak dikenali.'})

    if not P.milik(db, bimbingan_id, u.id):
        return JSONResponse({'ok': False,
                             'pesan': 'Link itu bukan milik Anda.'},
                            status_code=403)
    P.cabut(db, bimbingan_id, u.id)
    P.hitung_ulang_dicabut(db, u.id, bimbingan_id)
    log.info('[bagikan] bimbingan %s dicabut user=%s', bimbingan_id, u.id)
    return JSONResponse({'ok': True,
                         'pesan': 'Link sudah dimatikan. Catatan '
                                  'pembimbing tetap tersimpan.'})


# ═══════════════════════════════════════════════════════════════════════
#  LOG REVISI COMPACT (Tahap 2.3, ACC Bos 24Sep26)
# ═══════════════════════════════════════════════════════════════════════
#  Permintaan Bos: "Log Revisi compact (3 lapis lipatan)".
#
#  3 LAPIS itu:
#    LAPIS 1 — RINGKASAN  : 4 angka (total · belum selesai · sudah oke · hilang)
#    LAPIS 2 — PER MASALAH: 1 baris = 1 MASALAH (bukan 1 ronde)
#    LAPIS 3 — RANTAI     : ronde-ronde masalah itu (buka kalau perlu)
#
#  ⚠️ HANYA MEMBACA. Rute ini tidak mengubah apa pun.
#  ⚠️ Batas 5 MASALAH per permintaan supaya tidak berat di HP.

@router.get('/pembimbing/log/{bimbingan_id}')
def log_revisi(
    bimbingan_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Catatan pembimbing untuk mahasiswa — 3 lapis lipatan, hanya membaca."""
    u = _butuh_login(request, db)
    if not u:
        return JSONResponse({'ok': False, 'pesan': 'Sesi berakhir.'},
                            status_code=401)

    if not P.milik(db, bimbingan_id, u.id):
        return JSONResponse({'ok': False,
                             'pesan': 'Bimbingan itu bukan milik Anda.'},
                            status_code=403)

    b = db.get(P.Pembimbingan, bimbingan_id)
    if b is None:
        return JSONResponse({'ok': False, 'pesan': 'Bimbingan tidak ada.'})

    semua = P.daftar_catatan(db, bimbingan_id)
    simpul = P.rangkai(semua)
    angka = P.ringkas(semua)

    #  LAPIS 2: satu baris per MASALAH (bukan per ronde).
    baris = []
    for s in simpul:
        kepala = s['kepala']
        terbaru = s['terbaru']
        baris.append({
            'id': kepala.id,
            'berkas_id': kepala.berkas_id or 0,
            'masalah': (kepala.isi or '')[:200],
            'bagian': kepala.section_judul or '',
            'warna': terbaru.warna or 'kuning',
            'keadaan': terbaru.keadaan or 'utuh',
            'jumlah_ronde': s['jumlah_ronde'],
            #  ═══ LEWATI REVISI (Tahap 3.2, ACC Bos 24Sep26) ═══
            #  Kepala rantai = sumber kebenaran "masalah ini dilewati atau
            #  tidak". Dipakai layar untuk: (a) lencana "Revisi Dilewati",
            #  (b) mengunci ikon aksi selama masih dilewati.
            'dilewati': int(kepala.dilewati or 0),
            'dilewati_pada': (kepala.dilewati_pada.isoformat()
                              if kepala.dilewati_pada else ''),
            'diaktifkan_pada': (kepala.diaktifkan_pada.isoformat()
                                if kepala.diaktifkan_pada else ''),
            #  LAPIS 3: ronde-ronde masalah ini, tertua → terbaru.
            'ronde': [
                {
                    'ronde': c.ronde or 1,
                    'isi': (c.isi or '')[:300],
                    'warna': c.warna or 'kuning',
                    'keadaan': c.keadaan or 'utuh',
                    'tautan': c.tautan or '',
                    #  Lampiran komentar (nama disk) — dibawa frontend ke
                    #  panel AI supaya AI bisa membaca PDF/gambar contoh
                    #  dari pembimbing (ACC Bos 27Sep26).
                    'lampiran': ([c.lampiran] if c.lampiran else []),
                }
                for c in ([kepala] + s['anak'])
            ],
        })

    return JSONResponse({
        'ok': True,
        'nama_pembimbing': b.nama,
        'angka': angka,
        'baris': baris,
        'jumlah_baris': len(baris),
        #  Batas dari SATU sumber (server). JS tidak menyimpan angka sendiri.
        'batas_tampil': 5,
    })


# ═══════════════════════════════════════════════════════════════════════
#  LEWATI REVISI — sisi MAHASISWA (Tahap 3.2, ACC Bos 24Sep26)
#
#  Aturan Bos verbatim:
#   "Kalo mahasiswa klik melewati/ skip revisi. Maka akan muncul keterangan
#    'Revisi Dilewati' ini wajib untuk track history revisi. Dan bisa aktif
#    lagi jika pembimbing klik revisi (khusus untuk revisi yang di lewati
#    mahasiswa), jadi tetap Mahasiswa harus melakukan revisi lagi dan
#    tombol jadi aktif lagi di dashboard mahasiswa."
#
#  ⚠️ Rute ini HANYA boleh MELEWATI. Mengaktifkan kembali = hak PEMBIMBING
#     (ada di rute_pembimbing.py). Kalau digabung, mahasiswa bisa membuka
#     sendiri dan aturan Bos ("pembimbing klik revisi") jadi kosong.
# ═══════════════════════════════════════════════════════════════════════

@router.post('/pembimbing/lewati')
def lewati(
    request: Request,
    bimbingan_id: int = Form(0),
    catatan_id: int = Form(0),
    db: Session = Depends(get_db),
):
    """Mahasiswa melewati satu revisi. Jawaban JSON — layar tidak dimuat ulang."""
    u = _butuh_login(request, db)
    if not u:
        return JSONResponse({'ok': False, 'pesan': 'Sesi berakhir.'},
                            status_code=401)

    if not P.milik(db, bimbingan_id, u.id):
        return JSONResponse({'ok': False,
                             'pesan': 'Bimbingan itu bukan milik Anda.'},
                            status_code=403)

    berhasil, pesan = P.lewati(db, bimbingan_id, catatan_id, u.id)
    if not berhasil:
        return JSONResponse({'ok': False, 'pesan': pesan})

    semua = P.daftar_catatan(db, bimbingan_id)
    return JSONResponse({'ok': True, 'pesan': pesan,
                         'angka': P.ringkas(semua)})


# ═══════════════════════════════════════════════════════════════════════
#  KUNCI NASKAH (Tahap 3.3, ACC Bos 06Okt26 "A") — mahasiswa (pemilik)
#
#  Mahasiswa menyerahkan naskah ke penguji → tekan "Kunci Naskah" supaya
#  sorotan pembimbing disembunyikan (naskah terlihat bersih, bukan draft).
#  Boleh dikunci walau masih ada catatan belum selesai; yang muncul hanya
#  PERINGATAN (putusan Bos "A"), bukan larangan. Bisa dibuka lagi kapan saja.
# ═══════════════════════════════════════════════════════════════════════

@router.get('/pembimbing/kunci/{bimbingan_id}')
def status_kunci(
    bimbingan_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Keadaan kunci naskah (untuk menggambar tombol saat halaman dibuka)."""
    u = _butuh_login(request, db)
    if not u:
        return JSONResponse({'ok': False, 'pesan': 'Sesi berakhir.'},
                            status_code=401)
    if not P.milik(db, bimbingan_id, u.id):
        return JSONResponse({'ok': False,
                             'pesan': 'Bimbingan itu bukan milik Anda.'},
                            status_code=403)
    return JSONResponse({'ok': True, **P.status_kunci(db, bimbingan_id)})


@router.post('/pembimbing/kunci')
def kunci(
    request: Request,
    bimbingan_id: int = Form(0),
    paksa: int = Form(0),
    db: Session = Depends(get_db),
):
    """Kunci naskah. `paksa=1` = mahasiswa sudah membaca peringatan."""
    u = _butuh_login(request, db)
    if not u:
        return JSONResponse({'ok': False, 'pesan': 'Sesi berakhir.'},
                            status_code=401)
    if not P.milik(db, bimbingan_id, u.id):
        return JSONResponse({'ok': False,
                             'pesan': 'Bimbingan itu bukan milik Anda.'},
                            status_code=403)
    hasil = P.kunci(db, bimbingan_id, oleh_pembimbing=False, paksa=bool(paksa))
    return JSONResponse(hasil)


@router.post('/pembimbing/buka-kunci')
def buka_kunci(
    request: Request,
    bimbingan_id: int = Form(0),
    db: Session = Depends(get_db),
):
    """Buka kunci: catatan pembimbing tampil lagi."""
    u = _butuh_login(request, db)
    if not u:
        return JSONResponse({'ok': False, 'pesan': 'Sesi berakhir.'},
                            status_code=401)
    if not P.milik(db, bimbingan_id, u.id):
        return JSONResponse({'ok': False,
                             'pesan': 'Bimbingan itu bukan milik Anda.'},
                            status_code=403)
    return JSONResponse(P.buka_kunci(db, bimbingan_id))


@router.get('/pembimbing/arsip/{bimbingan_id}')
def arsip(
    bimbingan_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Arsip catatan: yang SUDAH SELESAI & lewat ARSIP_HARI hari.

    Terlipat dari daftar utama supaya daftar tetap segar (Tahap 3.3).
    Catatan TIDAK dihapus — hanya ditampilkan di panel terpisah.
    """
    u = _butuh_login(request, db)
    if not u:
        return JSONResponse({'ok': False, 'pesan': 'Sesi berakhir.'},
                            status_code=401)
    if not P.milik(db, bimbingan_id, u.id):
        return JSONResponse({'ok': False,
                             'pesan': 'Bimbingan itu bukan milik Anda.'},
                            status_code=403)

    semua = P.daftar_catatan(db, bimbingan_id, semuanya=True)
    batas = P._sekarang() - timedelta(days=ARSIP_HARI)
    tua = [c for c in semua
           if c.sudah_oke is not None and c.sudah_oke <= batas]
    return JSONResponse({
        'ok': True,
        'jumlah': len(tua),
        'hari': ARSIP_HARI,
        'butir': [
            {'id': c.id,
             'masalah': (c.isi or '')[:200],
             'bagian': c.section_judul or '',
             'selesai_pada': c.sudah_oke.isoformat() if c.sudah_oke else None}
            for c in tua
        ],
    })
