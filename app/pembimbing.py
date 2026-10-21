"""Kolaborasi PEMBIMBING pada naskah mahasiswa (ACC Bos 23Sep26, Tahap 1).

═══════════════════════════════════════════════════════════════════════════
POROS = PEMBIMBINGAN, BUKAN DOKUMEN (keputusan Bos)
═══════════════════════════════════════════════════════════════════════════
Kalau porosnya dokumen, maka mahasiswa mengganti naskah = SEMUA catatan
pembimbing hilang dari pandangan. Yang Bos mau: catatan menempel pada
HUBUNGAN BIMBINGAN. Naskah boleh berganti berkali-kali, catatan tetap ada.

    pembimbingan (1 baris = 1 hubungan mahasiswa ↔ pembimbing)
        ├── berkas yang pernah dibagikan  → pembimbingan_berkas
        └── catatan pembimbing            → catatan_pembimbing

TOKEN = SATU-SATUNYA KUNCI MASUK pembimbing (tanpa akun, tanpa sandi).
Karena itu token WAJIB:
  · 32+ karakter acak kriptografis (`secrets.token_urlsafe`) — tidak bisa ditebak;
  · punya MASA BERLAKU (`kedaluwarsa`) — Bos minta 7/30 hari;
  · bisa DICABUT kapan saja oleh mahasiswa (`dicabut`).
DILARANG memakai `random` biasa — bukan kriptografis.

═══════════════════════════════════════════════════════════════════════════
TABEL BARU SAJA — tidak ada tabel lama yang disentuh (tiang T2).
═══════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from .models import (
    BerkasPembimbingan,
    CatatanPembimbing,
    Pembimbingan,
    SessionLocal,
    User as _User,
)
from .config import ARSIP_HARI

log = logging.getLogger('eduai.pembimbing')

#  Alamat publik untuk link tinjau (dipakai saat menyusun link & pesan WA).
#  ⚠️ Satu sumber: jangan tulis alamat di kode lain. Kalau domain berubah,
#  cukup ubah di sini (atau di setelan EDUAI_BASE_PUBLIK pada .env).
BASE_PUBLIK = os.environ.get(
    'EDUAI_BASE_PUBLIK', 'https://eduai.bikinaja.id').rstrip('/')

#  Masa berlaku link yang boleh dipilih mahasiswa (hari). Bos: 7 atau 30.
MASA_BERLAKU = (7, 30)
#  Panjang token minimum. Kalau lebih pendek → TOLAK (bisa ditebak).
TOKEN_MIN = 32


def _sekarang() -> datetime:
    """Waktu UTC sadar-zona (jangan `utcnow()` — deprecated, hasilnya naif)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ══════════════════════════════════════════════════════════════════════════
# TOKEN
# ══════════════════════════════════════════════════════════════════════════

def buat_token() -> str:
    """Token rahasia acak KRIPTOGRAFIS (bukan `random`).

    `token_urlsafe(32)` → 43 karakter. Jauh di atas TOKEN_MIN.
    """
    return secrets.token_urlsafe(32)


def sidik_token(token: str) -> str:
    """Sidik SHA-256 token — supaya token MENTAH tidak disimpan di DB.

    KENAPA: kalau DB bocor, token mentah = pintu masuk langsung. Yang
    disimpan hanya sidik; token mentah hanya ada di URL yang dipegang
    mahasiswa & pembimbing. (Ini pola yang sama dengan sandi.)
    """
    return hashlib.sha256((token or '').encode('utf-8')).hexdigest()


def token_sah(token: str) -> bool:
    """Bentuk token masuk akal? Dipakai SEBELUM menyentuh DB."""
    if not token or len(token) < TOKEN_MIN:
        return False
    #  `token_urlsafe` hanya menghasilkan huruf, angka, '-' dan '_'.
    return all(c.isalnum() or c in '-_' for c in token)


# ══════════════════════════════════════════════════════════════════════════
# MAHASISWA — membuat & mengelola bimbingan
# ══════════════════════════════════════════════════════════════════════════

def buat_bimbingan(db: Session, user_id: int, nama: str,
                   hari: int = 7, wa: str = '', email: str = '',
                   file_id: int | None = None,
                   judul: str = '') -> tuple[Pembimbingan, str]:
    """Buat bimbingan baru. Return (baris, TOKEN MENTAH).

    ⚠️ TOKEN MENTAH HANYA ADA DI SINI. Setelah fungsi ini selesai, token
    tidak bisa diambil lagi dari DB (yang tersimpan cuma sidiknya). Mahasiswa
    WAJIB menyalin link saat itu — kalau hilang, tinggal buat link baru
    (dan link lama tetap hidup sampai masa berlakunya habis).

    `wa`/`email` = kontak pembimbing (permintaan Bos 23Sep26: mahasiswa isi
    Nama + No WA). TIDAK dipakai untuk login — hanya untuk mengirim link dan
    mengingatkan. ⚠️ JANGAN pernah menampilkan nomor ini ke pembimbing lain.
    """
    if hari not in MASA_BERLAKU:
        hari = MASA_BERLAKU[0]
    #  ⚠️ PENJAGA AKAR 24Sep26 (ACC Bos Opsi A):
    #     Rute /pembimbing/bagikan SUDAH menolak nama kosong, TAPI fungsi ini
    #     bisa dipanggil langsung (skrip, uji, kode lain) → nama kosong lolos
    #     dan tampil sebagai baris tanpa nama di daftar mahasiswa.
    #     Penjaga ditaruh DI SINI supaya SEMUA jalan masuk terlindungi.
    nama_bersih = (nama or '').strip()[:120]
    if not nama_bersih:
        raise ValueError('Nama pembimbing belum diisi.')
    token = buat_token()
    baris = Pembimbingan(
        user_id=user_id,
        nama=nama_bersih,
        wa=bersihkan_wa(wa),
        email=(email or '').strip()[:160],
        token_sidik=sidik_token(token),
        hari=hari,
        kedaluwarsa=_sekarang() + timedelta(days=hari),
    )
    db.add(baris)
    db.flush()                      # supaya baris.id ada untuk berkas

    #  🔔 Lonceng gelombang 2 #3 (27Sep26): link bimbingan siap.
    #     PENTING: pakai SESI UTAMA (catat() tak commit sendiri; commit
    #     dilakukan pemanggil rute — bukti 27Sep: sesi kedua = SQLite
    #     'database is locked' karena utama sedang pegang kunci tulis).
    #     commit sendiri HANYA bila pemanggil lupa — di rute sudah ada.
    try:
        from .notifikasi import catat as _ncatat
        _ncatat(db, user_id, 'pembimbing_diundang', nama=nama_bersih)
    except Exception as _e:                       # noqa: BLE001
        try:
            db.rollback()
        except Exception:                         # noqa: S110
            pass
        log.warning('[pembimbing] lonceng undangan gagal: %s', _e)

    #  Pemicu WA #2 (keputusan Bos 27Sep26): undangan pembimbing lewat WA —
    #  TEMPLATE BOS (verbatim): sebut nama pembimbing setelah "Meminta ijin,".
    #  Fire-and-forget: WA tidak sampai = bimbingan tetap sah.
    try:
        from . import wa as _wa
        _link = f'{BASE_PUBLIK}/tinjau/{token}'
        _judul = (judul or 'Naskah').strip()
        _wa.kirim_user(
            db, user_id, 'undangan',
            #  Template Bos 27Sep: sebut NAMA PEMBIMBING (penerima pesan)
            #  setelah "Meminta ijin," — bukan nama mahasiswa.
            f'Undangan Kolaborasi\n\n'
            f'Nama mahasiswa\n{nama_bersih}\n\n'
            f'Meminta ijin, {baris.nama} untuk menjadi pembimbing '
            f'dalam naskah :\n{_judul}\n\n'
            f'Melalui link berikut:\n{_link}\n\n'
            f'Berlaku {hari} hari.\nTerimakasih.')
    except Exception as _e:                       # noqa: BLE001
        log.warning('[pembimbing] WA undangan tidak terkirim: %s', _e)

    #  Kalau mahasiswa memilih naskah tertentu, langsung tautkan naskahnya.
    if file_id:
        tambah_berkas(db, baris, file_id, judul or 'Naskah', '')

    db.commit()
    db.refresh(baris)
    log.info('[pembimbing] bimbingan %s dibuat user=%s (%s hari, wa=%s)',
             baris.id, user_id, hari, 'ada' if baris.wa else 'kosong')
    return baris, token


def bersihkan_wa(nomor: str) -> str:
    """Rapikan nomor WhatsApp jadi bentuk 62xxxx (untuk tautan wa.me).

    0812-3456-7890 → 6281234567890.
    Handle semua gaya ketik mahasiswa (27Sep26, uji 17 kasus):
      +62..., 08..., 62..., 8..., spasi/strip/titik/kurung, link wa.me.
    Nomor terlalu pendek (<8 digit) atau tanpa angka → '' (ditolak jujur,
    JANGAN menebak — tebakan = WA nyasar ke orang lain).
    """
    angka = ''.join(c for c in (nomor or '') if c.isdigit())
    if not angka or len(angka) < 8:
        return ''
    if angka.startswith('62'):
        # +62 (0) 812... → 620812... : angka 0 setelah 62 adalah sisa
        # kebiasaan menulis kode area — buang supaya tidak jadi 620...
        while angka[2:3] == '0':
            angka = '62' + angka[3:]
        return angka
    if angka.startswith('0'):
        return '62' + angka[1:]
    if angka.startswith('8'):
        return '62' + angka
    return angka


def tautan_kirim(b: Pembimbingan, token: str, nama_mhs: str = '',
                 judul: str = '') -> str:
    """Tautan wa.me dengan pesan siap kirim (permintaan Bos 23Sep26).

    ⚠️ Isi pesan TIDAK boleh menyebut nama alat/AI (aturan Bos: nama alat
    tidak muncul di kolom kerja mahasiswa/pembimbing).
    """
    from urllib.parse import quote
    link = f'{BASE_PUBLIK}/tinjau/{token}'
    pesan = (
        f'Selamat pagi/siang, Bapak/Ibu {b.nama}.\n\n'
        f'Saya {nama_mhs or "mahasiswa Anda"}'
        + (f' dari {judul}' if judul else '')
        + ', mohon kesediaan Bapak/Ibu untuk meninjau naskah saya melalui '
        f'tautan berikut:\n\n{link}\n\n'
        'Bapak/Ibu dapat membaca naskah dan memberi catatan langsung pada '
        'bagian yang perlu diperbaiki. Terima kasih banyak.'
    )
    if not b.wa:
        return ''
    return f'https://wa.me/{b.wa}?text={quote(pesan)}'


def daftar_lengkap(db: Session, user_id: int) -> list[dict]:
    """Daftar bimbingan untuk DITAMPILKAN ke mahasiswa (tanpa token mentah).

    ⚠️ Token mentah TIDAK tersimpan di DB (cuma sidiknya) — jadi daftar ini
    TIDAK bisa menampilkan link lama. Link hanya terlihat SEKALI saat dibuat.
    Ini disengaja: kalau link bisa dilihat lagi kapan saja, penyimpanan token
    mentah jadi wajib, dan itu memperbesar risiko kalau DB bocor.
    """
    hasil = []
    for b in daftar_bimbingan(db, user_id):
        hasil.append({
            'id': b.id,
            'nama': b.nama,
            'wa': b.wa,
            'email': b.email,
            'hari': b.hari,
            'dibuat': b.dibuat,
            'kedaluwarsa': b.kedaluwarsa,
            'sisa_hari': sisa_hari(b),
            'dicabut': bool(b.dicabut),
            'aktif': (not b.dicabut) and sisa_hari(b) > 0,
            'dibuka_pada': b.dibuka_pada,
            'jumlah_berkas': (db.query(BerkasPembimbingan)
                              .filter(BerkasPembimbingan.pembimbingan_id == b.id)
                              .count()),
            'jumlah_catatan': (db.query(CatatanPembimbing)
                               .filter(CatatanPembimbing.pembimbingan_id == b.id,
                                       CatatanPembimbing.dibuang == 0)
                               .count()),
        })
    return hasil


def milik(db: Session, bimbingan_id: int, user_id: int) -> Pembimbingan | None:
    """Ambil bimbingan HANYA kalau memang milik mahasiswa ini.

    ⚠️ Pintu keamanan: mahasiswa TIDAK BOLEH melihat bimbingan orang lain.
    """
    return (db.query(Pembimbingan)
            .filter(Pembimbingan.id == bimbingan_id,
                    Pembimbingan.user_id == user_id)
            .one_or_none())


def daftar_bimbingan(db: Session, user_id: int) -> list[Pembimbingan]:
    """Semua bimbingan milik mahasiswa (yang terbaru di atas)."""
    return (db.query(Pembimbingan)
            .filter(Pembimbingan.user_id == user_id)
            .order_by(Pembimbingan.dibuat.desc())
            .all())


def cabut(db: Session, bimbingan_id: int, user_id: int) -> bool:
    """Cabut link (pengaman ke-3). Return True kalau berhasil.

    ⚠️ Cabut BUKAN hapus: catatan pembimbing TETAP ADA. Yang mati hanya
    pintu masuknya. Jadi kalau mahasiswa cabut lalu menyesal, catatannya
    tidak ikut hilang.
    """
    b = milik(db, bimbingan_id, user_id)
    if b is None or b.dicabut:
        return False
    b.dicabut = 1
    b.diubah = _sekarang()
    db.commit()
    log.info('[pembimbing] bimbingan %s DICABUT user=%s', bimbingan_id, user_id)
    return True


def hitung_ulang_dicabut(db: Session, user_id: int, bimbingan_id: int) -> bool:
    """Hidupkan lagi link yang sudah dicabut — TAPI masa berlakunya tidak
    diperpanjang. Kalau sudah lewat masa berlaku, tetap mati.

    KENAPA ada: mahasiswa kadang mencabut karena salah pencet. Jalan keluar
    yang jujur: boleh dihidupkan lagi, tapi tidak boleh jadi celah memperpanjang
    link tanpa membuat yang baru.
    """
    b = milik(db, bimbingan_id, user_id)
    if b is None:
        return False
    if b.kedaluwarsa <= _sekarang():
        return False                      # sudah lewat masa → tidak bisa
    b.dicabut = 0
    b.diubah = _sekarang()
    db.commit()
    return True


# ══════════════════════════════════════════════════════════════════════════
# PEMBIMBING — membuka link (TANPA akun, TANPA sandi)
# ══════════════════════════════════════════════════════════════════════════

#  Alasan link tidak bisa dibuka. Dipakai halaman untuk memilih kalimat
#  HANGAT + JALAN KELUAR (aturan Bos: dilarang kata menakutkan).
SEBAB_KEDALUWARSA = 'kedaluwarsa'
SEBAB_DICABUT = 'dicabut'
SEBAB_TIDAK_ADA = 'tidak_ada'


def cari_dari_token(db: Session, token: str) -> tuple[Pembimbingan | None, str]:
    """Cari bimbingan dari token link. Return (baris|None, sebab).

    ⚠️ URUTAN PEMERIKSAAN PENTING — dibalik bisa membocorkan informasi:
       1. bentuk token dulu (murah, tanpa DB);
       2. baru cocokkan sidik;
       3. baru periksa cabut/kedaluwarsa.
    Token yang tidak cocok SELALU menghasilkan sebab 'tidak_ada' yang sama —
    tidak dibedakan "token salah" vs "token hampir benar", supaya penebak
    tidak mendapat petunjuk.
    """
    if not token_sah(token):
        return None, SEBAB_TIDAK_ADA
    b = (db.query(Pembimbingan)
         .filter(Pembimbingan.token_sidik == sidik_token(token))
         .one_or_none())
    if b is None:
        return None, SEBAB_TIDAK_ADA
    if b.dicabut:
        return None, SEBAB_DICABUT
    if b.kedaluwarsa <= _sekarang():
        return None, SEBAB_KEDALUWARSA
    return b, ''


def catat_dibuka(db: Session, b: Pembimbingan, identitas: str | None = None) -> None:
    """Tandai pembimbing sudah membuka link (+ simpan identitas bila diisi).

    Identitas (HP/email) DIISI SEKALI saat pembukaan pertama — sesuai
    keputusan Bos: tanpa verifikasi, tanpa registrasi panjang. Kalau kolom
    sudah terisi, isian berikutnya TIDAK menimpa (biar tidak bisa diubah
    orang lain yang kebetulan memegang link).
    """
    berubah = False
    if b.dibuka_pada is None:
        b.dibuka_pada = _sekarang()
        berubah = True
    idn = (identitas or '').strip()[:160]
    if idn and not b.identitas:
        b.identitas = idn
        berubah = True
    if berubah:
        b.diubah = _sekarang()
        db.commit()


def sisa_hari(b: Pembimbingan) -> int:
    """Sisa masa berlaku dalam hari (0 = hari terakhir / sudah habis)."""
    delta = b.kedaluwarsa - _sekarang()
    return max(0, delta.days)


# ══════════════════════════════════════════════════════════════════════════
# NASKAH YANG DIBAGIKAN
# ══════════════════════════════════════════════════════════════════════════

def sidik_teks(teks: str) -> str:
    """Sidik naskah/teks — dipakai menjawab 'berubah atau belum' secara jujur."""
    return hashlib.sha256((teks or '').encode('utf-8')).hexdigest()


def tambah_berkas(db: Session, b: Pembimbingan, file_id: int | None,
                  judul: str, isi: str = '') -> BerkasPembimbingan:
    """Tambahkan naskah ke bimbingan. Link TIDAK berubah — tetap satu link.

    Kalau naskah dengan file_id sama sudah pernah dibagikan, baris itu
    DIPERBARUI (sidik baru) — bukan dibuat dobel.
    """
    baris = None
    if file_id:
        baris = (db.query(BerkasPembimbingan)
                 .filter(BerkasPembimbingan.pembimbingan_id == b.id,
                         BerkasPembimbingan.file_id == file_id)
                 .one_or_none())
    if baris is None:
        urut = (db.query(func.coalesce(func.max(BerkasPembimbingan.urutan), 0))
                .filter(BerkasPembimbingan.pembimbingan_id == b.id)
                .scalar() or 0) + 1
        baris = BerkasPembimbingan(pembimbingan_id=b.id, file_id=file_id,
                                   urutan=urut)
        db.add(baris)
    baris.judul = (judul or '').strip()[:200]
    baris.sidik = sidik_teks(isi)
    baris.diubah = _sekarang()
    db.commit()
    db.refresh(baris)
    return baris


def daftar_berkas(db: Session, bimbingan_id: int) -> list[BerkasPembimbingan]:
    """Naskah dalam satu bimbingan, urut sesuai tampilan (BAB I → III)."""
    return (db.query(BerkasPembimbingan)
            .filter(BerkasPembimbingan.pembimbingan_id == bimbingan_id)
            .order_by(BerkasPembimbingan.urutan, BerkasPembimbingan.id)
            .all())


def naskah_berubah(db: Session, baris: BerkasPembimbingan,
                   isi_sekarang: str) -> bool:
    """Apakah naskah SUDAH BERUBAH sejak dibagikan?

    ⚠️ INI PERTANYAAN JUJUR, bukan "sudah diperbaiki". Aplikasi TIDAK BOLEH
    mengklaim mahasiswa sudah memperbaiki sesuatu — yang bisa diketahui
    hanyalah teksnya berubah atau belum. Keputusan ada di pembimbing.
    """
    if not baris.sidik:
        return False
    return baris.sidik != sidik_teks(isi_sekarang)


# ══════════════════════════════════════════════════════════════════════════
# CATATAN PEMBIMBING (Tahap 1: simpan & baca saja)
# ══════════════════════════════════════════════════════════════════════════

def _kepala_rantai(db: Session, c: CatatanPembimbing) -> int:
    """Cari ID KEPALA rantai (induk paling atas) dari satu catatan.

    ⚠️ Ada batas 100 langkah + daftar `sudah` supaya TIDAK GANTUNG kalau
    data pernah rusak (induk melingkar). Kalau ketemu lingkaran, berhenti
    dan anggap yang sekarang sebagai kepala — lebih baik daripada hang.
    """
    sudah: set[int] = set()
    now = c
    for _ in range(100):
        if not now.induk_id or now.induk_id in sudah:
            break
        sudah.add(now.id)
        induk = (db.query(CatatanPembimbing)
                 .filter(CatatanPembimbing.id == now.induk_id,
                         CatatanPembimbing.pembimbingan_id == now.pembimbingan_id)
                 .one_or_none())
        if induk is None:
            break
        now = induk
    return now.id


def _ronde_berikutnya(db: Session, bimbingan_id: int, kepala_id: int) -> int:
    """Nomor ronde berikutnya untuk satu rantai.

    AKAR PERBAIKAN 24Sep26: dulu `induk.ronde + 1` — akibatnya ronde ke-3
    SELALU jadi 2 (karena semua anak menempel ke KEPALA yang rondenya 1).

    SEKARANG: ambil ronde TERBESAR di seluruh rantai, lalu + 1.
    Anggota rantai = kepala itu sendiri + semua keturunannya (anak, cucu,
    cicit — berapa pun dalamnya).
    """
    semua = (db.query(CatatanPembimbing)
             .filter(CatatanPembimbing.pembimbingan_id == bimbingan_id)
             .all())
    peta = {x.id: x for x in semua}

    #  Kumpulkan anggota rantai: mulai dari kepala, telusuri semua anak.
    anggota = {kepala_id}
    berubah = True
    while berubah:
        berubah = False
        for x in semua:
            if x.id in anggota:
                continue
            #  Naik ke atas: apakah salah satu leluhurnya ada di rantai ini?
            now = x
            sudah: set[int] = set()
            for _ in range(100):
                if not now.induk_id or now.id in sudah:
                    break
                sudah.add(now.id)
                if now.induk_id in anggota:
                    anggota.add(x.id)
                    berubah = True
                    break
                now = peta.get(now.induk_id)
                if now is None:
                    break

    terbesar = 1
    for x in semua:
        if x.id in anggota:
            terbesar = max(terbesar, x.ronde or 1)
    return terbesar + 1


def rapi_bab(teks: str) -> str:
    """'bab iii' / 'BAB III' / 'BAB 3' -> '3'  (satu bentuk untuk semua).

    KENAPA ADA: catatan pembimbing ditulis bebas — ada yang menulis 'BAB 3',
    ada yang 'bab iii'. Peta Jev memakai angka ('3'). Dengan seragam,
    catatan bisa dicocokkan ke peta tanpa Jev baru dan tanpa biaya.

    Kalau tidak dikenali -> KEMBALIKAN APA ADANYA (jangan menebak).
    """
    t = (teks or '').strip().upper().replace('BAB', '').strip()
    if t.isdigit():
        return t
    for n, r in ((1, 'I'), (2, 'II'), (3, 'III'), (4, 'IV'),
                 (5, 'V'), (6, 'VI'), (7, 'VII')):
        if t == r:
            return str(n)
    return (teks or '').strip()


def catat(db: Session, b: Pembimbingan, isi: str, *, section_id: str = '',
          section_judul: str = '', teks_asli: str = '', mulai: int = 0,
          akhir: int = 0, tautan: str = '', berkas_id: int | None = None,
          dari_pembimbing: bool = True,
          induk_id: int | None = None,
          lampiran: str = '', lampiran_nama: str = '') -> CatatanPembimbing:
    """Simpan satu catatan. Return barisnya.

    RANTAI: kalau `induk_id` diisi, catatan ini masuk RANTAI yang sama dan
    mendapat nomor ronde berikutnya. Revisi ke-2 tidak jadi catatan lepas —
    dia jadi ronde ke-2 dalam satu rantai. Begitu seterusnya.

    ⚠️ AKAR BUG DIPERBAIKI 24Sep26 (temuan uji Log Revisi, ACC Bos Opsi A):
       Dulu: `ronde = induk.ronde + 1`.
       AKIBATNYA: karena SEMUA ronde baru menempel ke KEPALA (bukan
       berantai ke ronde sebelumnya), ronde ke-3 dan seterusnya SELALU
       lahir sebagai ronde 2 — tidak pernah bisa lebih dari 2.
       Terukur: kepala(r1) · anak(r2) → ronde 2 ▸ anak(r3) → ronde 2 ❌
       SEHARUSNYA r3 = ronde 3.

       SEKARANG: ronde = (ronde TERBESAR di seluruh rantai) + 1.
       Rantai dicari dengan menelusuri ke KEPALA dulu (induk paling atas),
       lalu mengambil semua anggota rantai itu. Dengan begitu berapa pun
       dalamnya, nomornya benar dan tidak pernah bertabrakan.

    ⚠️ TIDAK ADA pemotongan kuota di sini. Catatan pembimbing TIDAK kena
    Token Revisi (keputusan lama). Kuota baru terpakai kalau mahasiswa
    memilih menjalankannya lewat AI.
    """
    ronde = 1
    kepala_id = None
    if induk_id:
        induk = (db.query(CatatanPembimbing)
                 .filter(CatatanPembimbing.id == induk_id,
                         CatatanPembimbing.pembimbingan_id == b.id)
                 .one_or_none())
        if induk is not None:
            kepala_id = _kepala_rantai(db, induk)
            ronde = _ronde_berikutnya(db, b.id, kepala_id)
        else:
            induk_id = None               # induk tidak sah → jangan dipakai

    txt = (teks_asli or '').strip()
    baris = CatatanPembimbing(
        pembimbingan_id=b.id,
        berkas_id=berkas_id,
        penulis_id=b.id if dari_pembimbing else None,
        induk_id=induk_id,
        ronde=ronde,
        section_id=rapi_bab(section_id)[:80],
        section_judul=(section_judul or '').strip()[:200],
        teks_asli=txt,
        sidik=sidik_teks(txt) if txt else '',
        mulai=int(mulai or 0),
        akhir=int(akhir or 0),
        dari_pembimbing=1 if dari_pembimbing else 0,
        warna='kuning' if dari_pembimbing else 'biru',
        isi=(isi or '').strip(),
        tautan=(tautan or '').strip()[:300],
        #  LAMPIRAN GAMBAR (Tahap 2.2). `lampiran` = nama berkas di disk
        #  (dibuat server, BUKAN dari user) → dibatasi ketat panjangnya.
        lampiran=(lampiran or '').strip()[:120],
        lampiran_nama=(lampiran_nama or '').strip()[:160],
        #  ⚠️ PERBAIKAN AKAR 24Sep26 (ACC Bos Opsi A):
        #     `keadaan` itu tentang SOROTAN (utuh | bergeser | hilang).
        #     Dulu: catatan TANPA sorotan (teks_asli kosong) diisi 'hilang'
        #     → mahasiswa melihat label "Naskah berubah" padahal naskahnya
        #     tidak berubah apa pun. Itu MENYESATKAN.
        #     Sekarang: catatan tanpa sorotan berkeadaan 'umum'
        #     → labelnya "Catatan umum" (jujur).
        #
        #  ⚠️⚠️ JEBAKAN YANG WULAN BARU SADARI 24Sep26 (temuan MATA):
        #     Angka ini HANYA nilai AWAL saat catatan dibuat. Ia TIDAK
        #     boleh dipercaya sebagai keadaan sekarang — naskah mahasiswa
        #     bisa berubah kapan saja. Yang dipakai layar adalah hasil
        #     hitung ULANG di `rute_pembimbing` (`sorotan_per_catatan`),
        #     sesuai putusan Bos "selalu segar".
        #     Kalau ada kode LAIN yang membaca `c.keadaan` langsung dari
        #     DB, itu BAHAYA: bisa menampilkan "utuh" padahal sudah hilang.
        keadaan='utuh' if txt else 'umum',
    )
    db.add(baris)
    db.commit()
    db.refresh(baris)
    return baris


def daftar_catatan(db: Session, bimbingan_id: int,
                   semuanya: bool = False) -> list[CatatanPembimbing]:
    """Catatan satu bimbingan (terbaru di atas).

    `semuanya=False` → yang SUDAH DIBUANG (soft-delete) tidak ditampilkan.
    `semuanya=True` → termasuk yang dibuang (untuk pemilik naskah/jejak).

    ⭐ 06Okt26 (Tahap 3.3 ARSIP >60 HARI): catatan yang SUDAH SELESAI
    (`sudah_oke` terisi) dan sudah lewat `ARSIP_HARI` hari DISEMBUNYIKAN
    dari daftar utama — tetap ada di DB, hanya tidak ditampilkan.
    Dengan `semuanya=True` arsip IKUT ditampilkan (untuk panel Arsip).
    """
    q = db.query(CatatanPembimbing).filter(
        CatatanPembimbing.pembimbingan_id == bimbingan_id)
    if not semuanya:
        q = q.filter(CatatanPembimbing.dibuang == 0)
        #  Arsip: sudah selesai + tua → sembunyikan dari daftar utama.
        batas = _sekarang() - timedelta(days=ARSIP_HARI)
        q = q.filter(~and_(
            CatatanPembimbing.sudah_oke.is_not(None),
            CatatanPembimbing.sudah_oke <= batas,
        ))
    return q.order_by(CatatanPembimbing.dibuat.desc()).all()


# ═══════════════════════════════════════════════════════════════════════
#  KUNCI NASKAH (Tahap 3.3, ACC Bos 06Okt26 "A")
#
#  MASALAH: naskah sudah dikirim ke penguji tapi masih ada sorotan kuning
#  → skripsi terlihat DRAFT. Rancangan menyebut ini "mosi paling bahaya".
#  SOLUSI: mahasiswa/pembimbing menekan "Kunci Naskah" → SEMUA sorotan
#  pembimbing disembunyikan. Catatan TIDAK dihapus — bisa dibuka lagi.
#  PERINGATAN (putusan Bos "A"): kalau masih ada catatan belum selesai,
#  TETAP BOLEH dikunci, tapi muncul peringatan jumlahnya — bukan larangan.
# ═══════════════════════════════════════════════════════════════════════

def status_kunci(db: Session, bimbingan_id: int) -> dict:
    """Keadaan kunci satu bimbingan + bahan peringatan saat mengunci.

    Bentuk: {'terkunci': bool, 'pada': datetime|None, 'oleh': int,
             'belum_selesai': int, 'pesan': str}
    `belum_selesai` = catatan kuning yang belum dilewati (masih harus
    dikerjakan) — dipakai untuk kalimat peringatan.
    """
    b = db.get(Pembimbingan, bimbingan_id)
    if b is None:
        return {'terkunci': False, 'pada': None, 'oleh': 0,
                'belum_selesai': 0, 'pesan': ''}
    kat = daftar_catatan(db, bimbingan_id)          # tanpa yang dibuang/arsip
    belum = [c for c in kat if c.warna == 'kuning' and not (c.dilewati or 0)]
    return {
        'terkunci': b.terkunci_pada is not None,
        #  ⚠️ ISO teks, BUKAN objek datetime — JSONResponse tidak bisa
        #  membuat JSON dari datetime (terukur: HTTP 500 di produksi).
        'pada': b.terkunci_pada.isoformat() if b.terkunci_pada else None,
        'oleh': b.terkunci_oleh or 0,
        'belum_selesai': len(belum),
        'pesan': _kalimat_kunci(b, len(belum)),
    }


def _kalimat_kunci(b: Pembimbingan, belum: int) -> str:
    """Kalimat peringatan/menyejukkan — JANGAN menuduh, sesuai gaya Bos."""
    if belum:
        return (f'Masih ada {belum} catatan yang belum ditindaklanjuti. '
                'Naskah tetap bisa dikunci, tapi catatan itu tersembunyi '
                'sampai kamu buka kuncinya lagi.')
    return ('Semua catatan sudah ditindaklanjuti. Aman dikunci sebelum '
            'diserahkan ke penguji.')


def kunci(db: Session, bimbingan_id: int, oleh_pembimbing: bool = False,
          paksa: bool = False) -> dict:
    """Kunci naskah: sembunyikan SEMUA sorotan pembimbing.

    `paksa` = menyatakan pemanggil sudah menerima peringatan (tombol
    "Ya, tetap kunci"). Tanpa `paksa`, kalau masih ada catatan belum
    selesai → TIDAK jadi mengunci, kembalikan `butuh_konfirmasi=True`.
    Catatan TIDAK dihapus; hanya `terkunci_pada` diisi.
    """
    b = db.get(Pembimbingan, bimbingan_id)
    if b is None:
        return {'ok': False, 'pesan': 'Bimbingan tidak ditemukan.'}
    kat = daftar_catatan(db, bimbingan_id)
    belum = [c for c in kat if c.warna == 'kuning' and not (c.dilewati or 0)]
    if belum and not paksa:
        return {'ok': False, 'butuh_konfirmasi': True, 'belum_selesai': len(belum),
                'pesan': _kalimat_kunci(b, len(belum))}
    b.terkunci_pada = _sekarang()
    b.terkunci_oleh = 1 if oleh_pembimbing else 0
    db.commit()
    db.refresh(b)
    log.info('[kunci] bimbingan=%s DIKUNCI (oleh %s, %d belum selesai)',
             bimbingan_id, 'pembimbing' if oleh_pembimbing else 'mahasiswa',
             len(belum))
    return {'ok': True, 'terkunci': True, 'belum_selesai': len(belum),
            'pesan': 'Naskah dikunci — semua catatan disembunyikan. '
                     'Buka kunci kalau perlu catatan lagi.'}


def buka_kunci(db: Session, bimbingan_id: int) -> dict:
    """Buka kunci: sorotan pembimbing muncul kembali (catatan utuh)."""
    b = db.get(Pembimbingan, bimbingan_id)
    if b is None:
        return {'ok': False, 'pesan': 'Bimbingan tidak ditemukan.'}
    b.terkunci_pada = None
    b.terkunci_oleh = 0
    db.commit()
    log.info('[kunci] bimbingan=%s DIBUKA lagi', bimbingan_id)
    return {'ok': True, 'terkunci': False,
            'pesan': 'Kunci dibuka — catatan pembimbing tampil lagi.'}


def bimbingan_terkunci(db: Session, bimbingan_id: int) -> bool:
    """Benar bila bimbingan ini sedang dikunci (dipakai saat menggambar
    sorotan di editor/pemirsa)."""
    b = db.get(Pembimbingan, bimbingan_id)
    return bool(b is not None and b.terkunci_pada is not None)


def rangkai(catatan: list[CatatanPembimbing]) -> list[dict]:
    """Susun catatan jadi RANTAI (induk → anak) untuk tampilan berlipat.

    KENAPA: tanpa ini, 12 catatan jadi 12 baris dan menumpuk. Bos minta
    history yang COMPACT: 1 baris = 1 MASALAH (bukan 1 ronde), rondenya
    masuk ke dalam.

    Return daftar dict: {kepala, ronde, jumlah_ronde, terbaru, anak[]}
    """
    peta = {c.id: c for c in catatan}
    akar: dict[int, dict] = {}
    for c in catatan:
        #  Cari kepala rantai (induk paling atas yang masih ada).
        kep = c
        dilihat = set()
        while kep.induk_id and kep.induk_id in peta and kep.induk_id not in dilihat:
            dilihat.add(kep.induk_id)
            kep = peta[kep.induk_id]
        simpul = akar.setdefault(kep.id, {
            'kepala': kep, 'ronde': kep.ronde or 1,
            'jumlah_ronde': 1, 'anak': [],
        })
        if c.id != kep.id:
            simpul['anak'].append(c)
            simpul['jumlah_ronde'] = max(simpul['jumlah_ronde'],
                                         (c.ronde or 1))
    hasil = list(akar.values())
    for s in hasil:
        s['anak'].sort(key=lambda x: (x.ronde or 1, x.id))
        s['terbaru'] = s['anak'][-1] if s['anak'] else s['kepala']
    hasil.sort(key=lambda s: s['terbaru'].dibuat, reverse=True)
    return hasil


def ringkas(catatan: list[CatatanPembimbing]) -> dict:
    """5 angka ringkasan untuk lapis 1 history (Bos minta: angka selalu jujur,
    termasuk yang terlipat).

    ⚠️ PERBAIKAN 24Sep26: `umum` (catatan tanpa sorotan) TIDAK dihitung
    sebagai 'hilang'. Dulu semua catatan umum masuk hitungan `hilang`
    → angka "Naskah berubah" membengkak dan menakutkan mahasiswa.

    ⚠️ TAMBAHAN 24Sep26 (Tahap 3.2 LEWATI REVISI, ACC Bos): angka ke-5
    `dilewati`. Aturan Bos: "Revisi Dilewati" WAJIB tercatat & WAJIB
    terlihat — jadi ia angka tersendiri, BUKAN dilebur ke 'belum'.
    Catatan yang dilewati TIDAK masuk 'belum' supaya mahasiswa & pembimbing
    tidak salah baca: 'belum' = masih harus dikerjakan SEKARANG,
    'dilewati' = mahasiswa minta lewat (menunggu putusan pembimbing).
    """
    belum = [c for c in catatan
             if c.warna == 'kuning' and not (c.dilewati or 0)]
    selesai = [c for c in catatan if c.warna == 'hijau']
    hilang = [c for c in catatan if c.keadaan == 'hilang']
    umum = [c for c in catatan if c.keadaan == 'umum']
    lewat = [c for c in catatan if (c.dilewati or 0)]
    return {
        'total': len(catatan),
        'belum': len(belum),
        'selesai': len(selesai),
        'hilang': len(hilang),
        'umum': len(umum),
        'dilewati': len(lewat),
    }


# ═══════════════════════════════════════════════════════════════════════
#  LEWATI REVISI (Tahap 3.2, ACC Bos 24Sep26)
#
#  ATURAN BOS (verbatim, JANGAN diubah tanpa ACC):
#   "Kalo mahasiswa klik melewati/ skip revisi. Maka akan muncul keterangan
#    'Revisi Dilewati' ini wajib untuk track history revisi. Dan bisa aktif
#    lagi jika pembimbing klik revisi (khusus untuk revisi yang di lewati
#    mahasiswa), jadi tetap Mahasiswa harus melakukan revisi lagi dan
#    tombol jadi aktif lagi di dashboard mahasiswa."
#
#  1) Mahasiswa boleh melewati → SIMPAN jejaknya (siapa tidak dicatat
#     karena catatan ini memang milik mahasiswa pemilik bimbingan).
#  2) HANYA PEMBIMBING yang bisa mengaktifkan kembali.
#  3) Setelah aktif kembali → catatan BARU (ronde+1) ditandai lewat
#     `induk_id`, persis pola rantai revisi yang sudah ada — jadi tidak
#     membongkar tabel & tidak menghapus riwayat.
# ═══════════════════════════════════════════════════════════════════════

def lewati(db: Session, bimbingan_id: int, catatan_id: int,
           user_id: int) -> tuple[bool, str]:
    """Mahasiswa melewati satu catatan (atau satu kepala rantai).

    Return (berhasil, pesan_jujur). Pesan dipakai apa adanya di layar —
    TIDAK ada kata 'gagal/error' (aturan bahasa Wulan).
    """
    b = db.get(Pembimbingan, bimbingan_id)
    if b is None or b.user_id != user_id:
        return False, 'Bimbingan itu bukan milik Anda.'

    c = (db.query(CatatanPembimbing)
         .filter(CatatanPembimbing.id == catatan_id,
                 CatatanPembimbing.pembimbingan_id == bimbingan_id)
         .one_or_none())
    if c is None:
        return False, 'Catatan itu tidak ditemukan.'

    #  Yang ditandai "dilewati" = SELURUH RANTAI masalah itu (kepala +
    #  anak-anaknya). Kalau hanya kepala yang ditandai, ronde di bawahnya
    #  tetap muncul sebagai "belum selesai" → mahasiswa bingung.
    semua = daftar_catatan(db, bimbingan_id)
    kepala_id = _kepala_rantai(db, c)
    target = [x for x in semua if _kepala_rantai(db, x) == kepala_id]

    sekarang = datetime.now(timezone.utc)
    for x in target:
        x.dilewati = 1
        x.dilewati_pada = sekarang
    db.commit()
    return True, ('Revisi ini ditandai dilewati dan tersimpan di riwayat. '
                  'Pembimbing bisa memintanya lagi kapan saja.')


def aktifkan_lagi(db: Session, bimbingan_id: int, catatan_id: int,
                  penulis_id: int | None = None) -> tuple[bool, str]:
    """PEMBIMBING mengaktifkan kembali revisi yang dilewati mahasiswa.

    Cara kerja: catatan yang dilewati dibersihkan tandanya, LALU dibuat
    catatan BARU (ronde+1) sebagai kepala rantai baru yang menunjuk ke
    catatan lama lewat `induk_id`. Hasilnya:
      • riwayat lama TIDAK hilang (catatan & `dilewati_pada` tetap ada)
      • di dashboard mahasiswa muncul sebagai permintaan BARU yang wajib
        dikerjakan lagi — perintah tidak tertimpa permintaan lama.
    """
    b = db.get(Pembimbingan, bimbingan_id)
    if b is None:
        return False, 'Bimbingan itu tidak ditemukan.'

    c = (db.query(CatatanPembimbing)
         .filter(CatatanPembimbing.id == catatan_id,
                 CatatanPembimbing.pembimbingan_id == bimbingan_id)
         .one_or_none())
    if c is None:
        return False, 'Catatan itu tidak ditemukan.'

    if not (c.dilewati or 0):
        return False, 'Catatan ini tidak sedang dilewati mahasiswa.'

    sekarang = datetime.now(timezone.utc)

    #  Bersihkan tanda 'dilewati' pada seluruh rantai (kalau ada anak),
    #  supaya tidak ada sisa tanda yang membuat layar salah baca.
    semua = daftar_catatan(db, bimbingan_id)
    kepala_id = _kepala_rantai(db, c)
    for x in semua:
        if _kepala_rantai(db, x) == kepala_id:
            x.dilewati = 0
            x.diaktifkan_pada = sekarang
            x.diaktifkan_oleh = penulis_id or 0

    #  Ronde baru sebagai permintaan yang hidup lagi.
    ronde_baru = _ronde_berikutnya(db, bimbingan_id, kepala_id) \
        if kepala_id != c.id else (c.ronde or 1) + 1

    #  ⚠️ CACAT YANG DITUTUP 24Sep26 (temuan uji 2 arah): `penulis_id`
    #  diisi angka yang BELUM TENTU ada di tabel `users` → SQLite menolak
    #  dengan 'FOREIGN KEY constraint failed' dan SELURUH aksi batal.
    #  Di lapangan ini bisa kejadian: catatan lama bisa punya penulis_id=0
    #  (fitur pembimbing baru ditambahkan 23Sep26). Obat: pakai pemilik
    #  bimbingan (mahasiswa, DIJAMIN ada) sebagai cadangan.
    #  ⚠️ Kenapa bukan menebak pembimbing lain: menulis nama orang yang
    #  tidak menulis catatan itu = memalsukan jejak. Pemilik bimbingan
    #  adalah pilihan jujur (dia pemilik naskahnya).
    id_penulis = penulis_id or c.penulis_id or 0
    if id_penulis:
        ada = db.query(_User).filter(_User.id == id_penulis).one_or_none()
        if ada is None:
            id_penulis = b.user_id
    else:
        id_penulis = b.user_id

    baru = CatatanPembimbing(
        pembimbingan_id=bimbingan_id,
        berkas_id=c.berkas_id,
        penulis_id=id_penulis,
        induk_id=kepala_id,
        ronde=ronde_baru,
        section_id=c.section_id or '',
        section_judul=c.section_judul or '',
        teks_asli=c.teks_asli or '',
        sidik=c.sidik or '',
        mulai=c.mulai or 0,
        akhir=c.akhir or 0,
        dari_pembimbing=1,
        warna='kuning',
        isi=c.isi or '',
        tautan=c.tautan or '',
        keadaan=c.keadaan or 'utuh',
    )
    db.add(baru)
    db.commit()
    return True, ('Revisi ini sudah diminta lagi ke mahasiswa. '
                  'Catatan lama tetap tersimpan di riwayat.')


