"""Rute halaman TINJAU untuk pembimbing (ACC Bos 23Sep26 — Tahap 1).

═══════════════════════════════════════════════════════════════════════════
ATURAN BESAR FILE INI
═══════════════════════════════════════════════════════════════════════════
1. HANYA LIHAT. Tidak ada satu rute pun di sini yang mengubah naskah
   mahasiswa. Pembimbing LIHAT naskah + catat. Naskah = milik mahasiswa.
   (tiang T1: halaman ini TIDAK menyentuh app/ai.py, tulis_docx.py, proses.py)

2. JANGAN pernah memakai `user_id` sesi saat melayani pembimbing — dia
   TIDAK punya user_id. Semua pembacaan lewat TOKEN. (celah #2 yang Wulan
   sebut ke Bos: kalau memakai user_id, catatan bisa menempel ke orang salah.)

3. Semua kalimat HANGAT + ada JALAN KELUAR. Dilarang kata menakutkan
   (aturan Bos: 'PERINGATAN/GAGAL/HABIS/BAHAYA' dilarang).

4. Keadaan link (kedaluwarsa / dicabut / tidak ada) SELALU memberi jalan
   keluar ke mahasiswa — bukan jalan buntu.
═══════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import logging

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Request,
                     UploadFile)
from fastapi.responses import (FileResponse, HTMLResponse,
                               RedirectResponse)
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import cari_bagian as CB
from . import kelompok_catatan as KC
from . import kolaborasi as kolab
from . import lampiran_pembimbing as LP
from . import pembimbing as P
from . import notifikasi as N
from .models import get_db

log = logging.getLogger('eduai.pembimbing.rute')

router = APIRouter()

#  ⚠️ Template engine dibuat oleh main.py supaya SATU sumber (folder template
#  + filter yang sama). Rute ini menerimanya lewat `pasang()`, bukan bikin
#  sendiri — kalau bikin sendiri, filter Jinja bisa berbeda dan tampilan rusak.
_tpl = None


def pasang(templates) -> None:
    """Dipanggil main.py: serahkan template engine miliknya."""
    global _tpl
    _tpl = templates


# ══════════════════════════════════════════════════════════════════════════
# KALIMAT HANGAT untuk link yang tidak bisa dibuka
# ══════════════════════════════════════════════════════════════════════════
#  Setiap kalimat: (1) tidak menyalahkan siapa pun, (2) menjelaskan apa yang
#  terjadi, (3) MEMBERI JALAN KELUAR. Tidak ada kata 'gagal/error/kedaluwarsa'.
KALIMAT_LINK = {
    P.SEBAB_KEDALUWARSA: {
        'judul': 'Link ini sudah lewat masa berlakunya',
        'isi': 'Link tinjauan biasanya berlaku 7 atau 30 hari supaya naskah '
               'mahasiswa tetap terjaga. Masa berlakunya sudah selesai.',
        'jalan': 'Minta mahasiswa mengirim link baru — prosesnya sebentar, '
                 'kok. Catatan yang pernah Anda tulis tetap tersimpan.',
    },
    P.SEBAB_DICABUT: {
        'judul': 'Link ini sudah tidak aktif',
        'isi': 'Mahasiswa sudah menutup link yang ini. Biasanya karena naskah '
               'sudah selesai ditinjau, atau karena link-nya diganti yang baru.',
        'jalan': 'Kalau masih perlu, minta mahasiswa mengirim link baru. '
                 'Catatan lama Anda tetap ada.',
    },
    P.SEBAB_TIDAK_ADA: {
        'judul': 'Link ini tidak dapat dibuka',
        'isi': 'Alamat link-nya terpotong saat dikirim, atau bukan '
               'alamat yang lengkap.',
        'jalan': 'Coba buka lagi dari pesan aslinya (jangan dari salinan), '
                 'atau minta mahasiswa mengirim ulang.',
    },
}


# ══════════════════════════════════════════════════════════════════════════
# HALAMAN PEMBIMBING
# ══════════════════════════════════════════════════════════════════════════

@router.get('/tinjau/{token}', response_class=HTMLResponse)
def halaman_tinjau(token: str, request: Request,
                   lampiran_ditolak: str = '',
                   db: Session = Depends(get_db)):
    """Halaman tinjau pembimbing — HANYA LIHAT.

    Kalau link tidak bisa dibuka TIDAK dilempar 404. Yang terjadi: halaman
    ramah + jalan keluar. (Aturan Bos: jangan ada jalan buntu.)
    """
    b, sebab = P.cari_dari_token(db, token)
    if b is None:
        k = KALIMAT_LINK.get(sebab, KALIMAT_LINK[P.SEBAB_TIDAK_ADA])
        log.info('[pembimbing] link tidak bisa dibuka: %s', sebab)
        return _tpl.TemplateResponse('tinjau_maaf.html', {
            'request': request, 'k': k, 'sebab': sebab,
        })

    #  Tandai sudah dibuka (bukti pembimbing pernah masuk).
    pertama = (b.dibuka_pada is None)
    P.catat_dibuka(db, b)

    #  🤝 27Sep26 (T5.1 Opsi A): pembimbing yang SUDAH punya akun → simpan
    #  token ini ke Setelan (kunci kolaborasi_token_<id>) supaya tombol
    #  "Buka tinjauan" di /kolaborasi selalu bisa dipakai. Keamanan: token
    #  memang sudah pernah keluar di URL; disimpan hanya bila bimbingan
    #  mengundang email akun ini (atau identitas masih kosong → kaitkan).
    try:
        from .main import user_dari_request as _udr   # hindari import lingkar
        _u = _udr(request, db)
        if _u is not None:
            _ok, _s = kolab.kaitkan_token(db, token, _u)
            if _ok:
                from .models import Setelan
                _kunci = f'kolaborasi_token_{b.id}'
                _set = db.scalars(
                    select(Setelan).where(Setelan.kunci == _kunci)).first()
                if _set:
                    _set.nilai = token
                else:
                    db.add(Setelan(kunci=_kunci, nilai=token))
                db.commit()
    except Exception as e:                                 # noqa: BLE001
        log.warning('[pembimbing] kaitan akun gagal (tidak fatal): %s', e)

    #  🔔 LONCENG PEMBIMBING #2 (26Sep26, ACC Bos): pembimbing PERTAMA
    #  kali membuka naskah → kabari pemilik. Sekali seumur bimbingan
    #  (kunci anti-spam + syarat `pertama`), bukan tiap kunjungan.
    if pertama:
        try:
            N.catat(db, b.user_id, 'pembimbing_membuka')
            db.commit()   # catat() tidak commit sendiri — lihat hook #1
        except Exception as e:                                 # noqa: BLE001
            log.warning('[pembimbing] notifikasi dibuka gagal: %s', e)

    berkas = P.daftar_berkas(db, b.id)
    catatan = P.daftar_catatan(db, b.id)
    rantai = P.rangkai(catatan)
    angka = P.ringkas(catatan)

    #  ── TAHAP 2.5b (ACC Bos 24Sep26): ARAHKAN NASKAH KE CATATAN ────────
    #  Perintah Bos: "saat klik revisi juga langsung menuju halaman revisi
    #  yang dimaksud, jadi Pembimbing di mudahkan untuk cek revisian naskah."
    #
    #  KENAPA DI HITUNG DI SERVER: naskah bisa 400rb karakter. Kalau seluruh
    #  naskah dikirim ke browser hanya untuk dicari, halaman jadi berat.
    #  Jadi pencarian dilakukan SEKALI di sini, hasilnya (kutipan pendek)
    #  yang dikirim ke template.
    #
    #  ⚠️ JUJUR: kalau tidak ketemu, `petunjuk[simpul.id]` tetap None dan
    #  template WAJIB memberi tahu pembimbing apa adanya — bukan diam-diam
    #  tidak bergerak.
    naskah_per_berkas = {}
    for bk in berkas:
        naskah_per_berkas[bk.id] = _isi_naskah(db, bk)
    petunjuk = {}
    for simpul in (rantai or []):
        c = simpul.get('terbaru')
        if c is None:
            continue
        #  ⚠️ KUNCI memakai `c.id` (catatan terbaru), BUKAN `simpul['id']`.
        #  `rangkai()` TIDAK menyediakan kunci 'id' di simpul — ia hanya
        #  memberi kepala/ronde/jumlah_ronde/anak/terbaru. Kesalahan memakai
        #  simpul.get('id') membuat SEMUA catatan dapat None → seluruh baris
        #  tampil "Tidak ditemukan bagiannya" padahal bagiannya ADA.
        #  (Bug nyata 24Sep26, ketemu dari potret+MATA, bukan dari uji teks.)
        bk_id = getattr(c, 'berkas_id', None)
        pilih = ([naskah_per_berkas.get(bk_id, '')] if bk_id
                 else [naskah_per_berkas.get(x.id, '') for x in berkas])
        try:
            petunjuk[c.id] = CB.cari_di_banyak(
                pilih, c.isi or '', getattr(c, 'teks_asli', '') or '')
        except Exception as e:                                 # noqa: BLE001
            log.warning('[pembimbing] pencarian bagian gagal: %s', e)
            petunjuk[c.id] = None

    #  ── TAHAP 3.1 (ACC Bos 24Sep26): PERIKSA SOROTAN SETIAP DIBUKA ─────
    #  Putusan Bos: "Saat pembimbing BUKA halaman (selalu segar)".
    #
    #  KENAPA DIPERIKSA ULANG DAN TIDAK DISIMPAN: mahasiswa bisa mengubah
    #  naskahnya kapan saja. Kalau keadaan sorotan disimpan dulu (mis.
    #  'utuh' saat catatan dibuat), lalu mahasiswa menghapus kalimatnya,
    #  pembimbing akan melihat "menempel" padahal sudah hilang — itu
    #  MENYESATKAN. Jadi keadaan dihitung dari naskah yang ADA SEKARANG.
    #
    #  ATURAN INDUK (keputusan Bos, terkunci): sumber kebenaran = DATABASE.
    #  Sorotan hilang → catatan TETAP ADA, pembimbing tetap diberi tahu.
    #  Fungsi `sorotan.cari_sorotan()` TIDAK menyimpan apa pun — hanya baca.
    sorotan_per_catatan = {}
    try:
        from . import sorotan as SR
        for bk in berkas:
            naskah_bk = naskah_per_berkas.get(bk.id, '')
            for c in catatan:
                if getattr(c, 'berkas_id', None) not in (None, bk.id):
                    continue
                kunci = c.id
                #  Naskah pertama yang punya berita menang; kalau catatan
                #  tidak menempel ke berkas tertentu, dipakai berkas pertama.
                if kunci not in sorotan_per_catatan and not naskah_bk:
                    continue
                hasil = SR.cari_sorotan(naskah_bk, c.teks_asli or '')
                #  ⚠️ AKAR BUG 24Sep26 (temuan MATA, bukan uji teks):
                #  Dulu hasil ini TIDAK memuat `berkas`. Padahal JS di layar
                #  menuntut `s.berkas` untuk mencocokkan paragraf:
                #     if (String(s.berkas) !== String(berkas)) return;
                #  Karena `undefined !== "9"` SELALU benar, SEMUA paragraf
                #  dilewati → tanda 🟡 TIDAK PERNAH muncul, walau datanya
                #  lengkap dan HTML-nya `par-ada-catatan` = 2.
                #  Uji teks lolos (HTML benar), MATA yang menemukan.
                hasil['berkas'] = bk.id
                sorotan_per_catatan[kunci] = hasil
    except Exception as e:                                     # noqa: BLE001
        #  Sorotan = lapisan bantu. Kalau gagal, halaman pembimbing WAJIB
        #  tetap terbuka (jangan 500). Catatan tetap tampil.
        log.warning('[pembimbing] gagal periksa sorotan: %s', e)
        sorotan_per_catatan = {}

    #  ── TAHAP 2.5 (ACC Bos 24Sep26): KELOMPOKKAN CATATAN PER BAB ──────
    #  Masalah yang dipecahkan (kata Bos): catatan pembimbing lama-lama
    #  banyak & panel samping sempit jadi tidak nyaman. Solusinya:
    #  kelompok per bab, satu bab terbuka (yang paling banyak catatan baru).
    #
    #  ⚠️ Kalau naskah TIDAK punya bab (perjanjian, nota, dokumen umum,
    #  artikel jurnal tanpa kata "BAB") → kelompok PER HARI + kotak ketik
    #  tetap disediakan. JANGAN sampai pembimbing tidak bisa menulis bab.
    bab_naskah: list[dict] = []
    for bk in berkas:
        try:
            bab_naskah = KC.daftar_bab_naskah(_isi_naskah(db, bk))
        except Exception as e:                                 # noqa: BLE001
            log.warning('[pembimbing] gagal deteksi bab: %s', e)
            bab_naskah = []
        if bab_naskah:
            break          # pakai naskah PERTAMA yang punya bab

    kelompok = KC.kelompokkan(rantai, ada_bab=bool(bab_naskah))

    return _tpl.TemplateResponse('tinjau.html', {
        'request': request,
        'token': token,
        'nama_mhs': _nama_mahasiswa(db, b.user_id),
        'nama_pembimbing': b.nama,
        'berkas': berkas,
        'catatan': catatan,
        'rantai': rantai,
        'kelompok': kelompok,
        'bab_naskah': bab_naskah,
        'petunjuk': petunjuk,
        'sorotan': sorotan_per_catatan,
        'angka': angka,
        'sisa_hari': P.sisa_hari(b),
        'sudah_isi_identitas': bool(b.identitas),
        #  Tahap 2.2: pembimbing diberi tahu kalau gambarnya ditolak,
        #  supaya tidak diam-diam mengira gambarnya terkirim.
        'lampiran_ditolak': bool(lampiran_ditolak),
        #  🆕 03Okt26: alat pembimbing (Buka di editor + Periksa dengan AI).
        #  Hanya PENANDA TAMPILAN — pagar sebenarnya di rute & modul
        #  pembimbing_ai (server), bukan di sini.
        'ai_aktif': _ai_aktif(),
    })


def _ai_aktif() -> bool:
    """Saklar alat pembimbing (config). Aman kalau modelnya belum ada."""
    try:
        from . import pembimbing_ai as PAI
        return PAI.aktif()
    except Exception:                                          # noqa: BLE001
        return False


def _nama_mahasiswa(db: Session, user_id: int) -> str:
    """Nama mahasiswa pemilik naskah (dipakai halaman sambutan).

    ⚠️ Hanya NAMA — jangan bocorkan email/HP/kouta mahasiswa ke pembimbing.
    """
    from .models import User
    u = db.query(User).filter(User.id == user_id).one_or_none()
    if u is None:
        return 'Mahasiswa'
    return (getattr(u, 'nama', '') or getattr(u, 'email', '') or 'Mahasiswa')


@router.get('/tinjau/{token}/naskah/{berkas_id}', response_class=HTMLResponse)
def baca_naskah(token: str, berkas_id: int, db: Session = Depends(get_db)):
    """Baca ISI naskah satu bagian — TEKS POLOS, HANYA BACA.

    KENAPA teks polos, bukan HTML: (1) halaman pembimbing jadi ringan walau
    naskahnya besar; (2) isi naskah TIDAK BISA menyuntikkan kode ke halaman
    (template memakai `textContent`, bukan `innerHTML`).

    ⚠️ HANYA BACA. Rute ini tidak boleh punya efek samping apa pun pada
    naskah mahasiswa — tidak menyimpan, tidak mengubah versi, tidak
    memanggil AI.
    """
    b, sebab = P.cari_dari_token(db, token)
    if b is None:
        return HTMLResponse('', status_code=403)

    #  ⚠️ Pastikan berkas ini MEMANG milik bimbingan ini. Tanpa pemeriksaan
    #  ini, pembimbing bisa membaca naskah mahasiswa lain hanya dengan
    #  menebak angka berkas_id.
    from .models import BerkasPembimbingan
    bk = (db.query(BerkasPembimbingan)
          .filter(BerkasPembimbingan.id == berkas_id,
                  BerkasPembimbingan.pembimbingan_id == b.id)
          .one_or_none())
    if bk is None:
        return HTMLResponse('', status_code=404)

    teks = _isi_naskah(db, bk)
    return HTMLResponse(teks)


#  ══════════════════════════════════════════════════════════════════════
#  PEMBANTU: memisahkan NASKAH dari CATATAN AI (akar diperbaiki 24Sep26)
#  ══════════════════════════════════════════════════════════════════════
#  KENAPA PERLU: `versi_dokumen` menampung DUA jenis isi yang berbeda —
#  (a) NASKAH mahasiswa (yang Bos mau dibaca pembimbing), dan
#  (b) CATATAN / HASIL REVISI AI (yang ditulis mesin, mis. "saran perbaikan").
#  Dulu keduanya dianggap sama → pembimbing bisa membaca CATATAN AI dan
#  menyangkanya naskah mahasiswa. Itu menyesatkan DAN membuat deteksi bab
#  mustahil (dropdown kosong).
#
#  CIRI yang dipakai = jalur `bab='__seluruh__'` (penanda mesin revisi untuk
#  perbaikan menyeluruh) + pembuka khas laporan revisi. Sengaja dipakai
#  BEBERAPA ciri: satu ciri saja rapuh kalau format mesin berubah.
CIRI_BAB_CATATAN = ('__seluruh__', '__catatan__', '__umum__')
CIRI_AWAL_CATATAN = ('───── BAGIAN', 'BAGIAN 1 DARI', 'Komentar ini menuntut',
                     'Komentar ini menyoroti', 'Berikut titik-titik',
                     'salah → benar', 'Saran perbaikan')


def _kelihatan_catatan_ai(v) -> bool:
    """True kalau baris `versi_dokumen` ini CATATAN AI, bukan naskah.

    ⚠️ SENGAJA KONSERVATIF (hanya bilang "catatan" kalau buktinya kuat).
    Salah menuduh naskah sebagai catatan = pembimbing kehilangan naskahnya —
    itu lebih merugikan daripada membiarkan catatan lolos.
    """
    bab = (getattr(v, 'bab', '') or '').strip().lower()
    if bab in CIRI_BAB_CATATAN:
        return True
    awal = (getattr(v, 'isi', '') or '').lstrip()[:80]
    return any(awal.startswith(c) for c in CIRI_AWAL_CATATAN)


def _baca_berkas_asli(p, nama: str) -> str:
    """Baca berkas ASLI mahasiswa dari disk jadi teks.

    Dipakai sebagai jalan terakhir saat DB tidak memuat naskah. Pembaca
    memakai mesin yang SUDAH ADA di EduAi (`ai._teks_dari_berkas`) supaya
    PDF/Word/DOCX tertangani tanpa library tambahan — kontainer produksi
    memang tidak punya python-docx.
    """
    try:
        from . import ai as AI
        return AI._teks_dari_berkas(p, nama)                    # noqa: SLF001
    except Exception as e:                                     # noqa: BLE001
        log.warning('[pembimbing] gagal baca berkas asli %s: %s', p, e)
        return ''


def _isi_naskah(db: Session, bk) -> str:
    """Ambil teks naskah untuk dibaca pembimbing.

    ══════════════════════════════════════════════════════════════════════
    🔴 AKAR DIPERBAIKI 24Sep26 (ACC Bos: "Opsi A")

    MASALAH YANG BOS TEMUKAN: dropdown "Bagian mana?" TIDAK PRESISI pada
    naskah nyata — 18 naskah nyata diuji, hampir semua dapat 0 bab.

    AKARNYA: fungsi ini DULU mengambil `versi_dokumen` TERAKHIR apa saja,
    TANPA memeriksa isinya. Ternyata `versi_dokumen` TIDAK SELALU naskah —
    banyak barisnya berisi **CATATAN/HASIL REVISI AI** (ditandai
    `bab='__seluruh__'` dan isinya diawali "───── BAGIAN 1 dari 2 ─────").
    Akibatnya halaman pembimbing membaca CATATAN AI dan menyebutnya
    "naskah mahasiswa" → deteksi bab mustahil → dropdown kosong.

    PERBAIKAN (di akar, bukan tambalan):
      1. Tolak versi yang JELAS catatan (penanda `CIRI_CATATAN_AI`).
      2. Pilih versi TERPANJANG yang bukan catatan — bukan sekadar terbaru.
         (Versi naskah utuh selalu lebih panjang dari catatan.)
      3. Kalau tetap tidak ada naskah di DB → pakai BERKAS ASLI di disk
         (UPLOAD_DIR/<user_id>/<nama_simpan>) — ini naskah sebenarnya.
      4. Kalau dua-duanya tidak ada → jujur kembalikan '' (halaman memberi
         tahu pembimbing), JANGAN menampilkan catatan AI sebagai naskah.

    ⚠️ HANYA BACA. Tidak menyimpan, tidak menyentuh mesin revisi.
    ══════════════════════════════════════════════════════════════════════
    """
    from .models import FileBerkas, VersiDokumen

    #  ── 1. Cari versi dokumen yang benar-benar berisi NASKAH ───────────
    try:
        if bk.file_id:
            kandidat = (db.query(VersiDokumen)
                        .filter(VersiDokumen.file_id == bk.file_id)
                        .all())
            bersih = [v for v in kandidat
                      if (v.isi or '').strip()
                      and not _kelihatan_catatan_ai(v)]
            if bersih:
                #  versi naskah TERPANJANG = paling lengkap
                v = max(bersih, key=lambda x: len(x.isi or ''))
                return v.isi
    except Exception as e:                                     # noqa: BLE001
        log.warning('[pembimbing] gagal baca versi dokumen %s: %s', bk.id, e)

    #  ── 2. Tidak ada naskah di DB → pakai BERKAS ASLI di disk ──────────
    try:
        import os
        from pathlib import Path
        if bk.file_id:
            f = (db.query(FileBerkas)
                 .filter(FileBerkas.id == bk.file_id).one_or_none())
            if f is not None:
                from .main import UPLOAD_DIR
                for p in (Path(UPLOAD_DIR) / str(f.user_id) / f.nama_simpan,
                          Path(getattr(f, 'jalur', '') or '')):
                    if p and p.is_file():
                        return _baca_berkas_asli(p, f.nama)
    except Exception as e:                                     # noqa: BLE001
        log.warning('[pembimbing] gagal baca berkas %s: %s', bk.id, e)

    #  ── 3. Jujur kosong (halaman memberi tahu pembimbing) ──────────────
    return ''


@router.post('/tinjau/{token}/identitas')
def simpan_identitas(token: str, identitas: str = Form(''),
                     db: Session = Depends(get_db)):
    """Pembimbing isi HP/email → LANGSUNG masuk (TANPA verifikasi).

    Keputusan Bos: registrasi panjang bikin pembimbing menutup halaman.
    Pengamannya bukan verifikasi, tapi: (1) yang bisa dilakukan cuma LIHAT
    naskah yang link-nya dia pegang; (2) memakai AI butuh token berbayar.
    """
    b, sebab = P.cari_dari_token(db, token)
    if b is None:
        return RedirectResponse(f'/tinjau/{token}', status_code=303)
    P.catat_dibuka(db, b, identitas)
    return RedirectResponse(f'/tinjau/{token}', status_code=303)


@router.post('/tinjau/{token}/catatan')
def tambah_catatan(token: str, isi: str = Form(''), section_id: str = Form(''),
                   section_judul: str = Form(''), teks_asli: str = Form(''),
                   section_teks: str = Form(''), tautan: str = Form(''),
                   induk_id: str = Form(''), berkas_id: str = Form(''),
                   nomor_paragraf: str = Form(''),
                   lampiran: UploadFile | None = File(None),
                   db: Session = Depends(get_db)):
    """Pembimbing menulis catatan pada satu bagian naskah.

    ⚠️ CATATAN TIDAK MEMOTONG KUOTA APA PUN. Token Revisi baru terpakai
    kalau mahasiswa memilih menjalankannya lewat AI (keputusan lama).
    ⚠️ Rute ini TIDAK menyentuh naskah — hanya menambah baris catatan.
    ⚠️ LAMPIRAN GAMBAR (Tahap 2.2): kalau gambarnya ditolak (jenis/ukuran),
    CATATAN TETAP DISIMPAN. Jangan buang tulisan pembimbing hanya karena
    lampirannya bermasalah — itu menghilangkan pekerjaan orang.

    ── TAHAP 3.1 (ACC Bos 24Sep26) — SOROTAN KALIMAT ──────────────────
    `berkas_id` + `nomor_paragraf`: pembimbing KLIK satu kalimat di naskah,
    jadi kita tahu persis paragraf mana yang dimaksud. `teks_asli` =
    kalimat yang benar-benar ada di naskah (dikirim layar, bukan diketik
    pembimbing) → itu yang jadi KENANGAN teks di DB.

    ⚠️ Kalimat diambil dari naskah yang SUDAH dimuat layar. Server TIDAK
    mempercayai angka dari browser untuk menentukan isi; yang disimpan
    hanya `teks_asli` (teks), dan keadaan sorotan DIPERIKSA ULANG setiap
    halaman dibuka — jadi angka yang salah pun tidak membuat data rusak.
    """
    b, sebab = P.cari_dari_token(db, token)
    if b is None:
        return RedirectResponse(f'/tinjau/{token}', status_code=303)

    induk = None
    try:
        induk = int(induk_id) if (induk_id or '').strip() else None
    except ValueError:
        induk = None

    #  ── Berkas & paragraf tempat sorotan menempel (Tahap 3.1) ────────
    #  ⚠️ WAJIB diperiksa: berkas itu harus MILIK bimbingan ini. Tanpa
    #  pemeriksaan ini, pembimbing bisa menempelkan catatan ke naskah
    #  mahasiswa lain hanya dengan menebak angka.
    bk_terpilih = None
    try:
        if (berkas_id or '').strip():
            from .models import BerkasPembimbingan
            bk_terpilih = (db.query(BerkasPembimbingan)
                           .filter(BerkasPembimbingan.id == int(berkas_id),
                                   BerkasPembimbingan.pembimbingan_id == b.id)
                           .one_or_none())
    except (ValueError, TypeError):
        bk_terpilih = None

    #  `mulai`/`akhir` = posisi kalimat DI DALAM paragraf itu. Dihitung
    #  ULANG di server dari teks_asli (jangan percaya angka dari browser).
    mulai_n, akhir_n = 0, 0
    if bk_terpilih is not None and (teks_asli or '').strip():
        try:
            from . import sorotan as SR
            hasil = SR.cari_sorotan(_isi_naskah(db, bk_terpilih), teks_asli)
            if hasil.get('nomor') is not None:
                mulai_n = int(hasil.get('awal') or 0)
                akhir_n = int(hasil.get('akhir') or 0)
        except Exception as e:                                 # noqa: BLE001
            log.warning('[pembimbing] gagal hitung posisi sorotan: %s', e)

    #  ── Lampiran (opsional) ──
    nama_disk, nama_tampil = '', ''
    if lampiran is not None and (lampiran.filename or '').strip():
        try:
            nama_disk, nama_tampil = LP.simpan(lampiran)
        except ValueError as e:
            #  Gambar ditolak → catatannya TETAP lanjut, tapi pembimbing
            #  diberi tahu lewat tanda di halaman (bukan hilang diam-diam).
            log.info('[pembimbing] lampiran ditolak: %s', e)
            return RedirectResponse(f'/tinjau/{token}?lampiran_ditolak=1',
                                    status_code=303)

    if ((isi or '').strip() or (tautan or '').strip()
            or nama_disk):
        P.catat(db, b, isi, section_id=section_id, section_judul=section_judul,
                teks_asli=teks_asli, tautan=tautan, induk_id=induk,
                mulai=mulai_n, akhir=akhir_n,
                berkas_id=(bk_terpilih.id if bk_terpilih is not None else None),
                lampiran=nama_disk, lampiran_nama=nama_tampil)

        #  🔔 LONCENG PEMBIMBING #1 (26Sep26, ACC Bos): kabari pemilik
        #  naskah ada catatan baru. Penerima = b.user_id. Sifatnya opsional —
        #  gagal kirim TIDAK menggagalkan catatan (catat() tak pernah lempar).
        try:
            N.catat(db, b.user_id, 'pembimbing_catatan_baru',
                    jeda_jam=1,
                    jumlah=1, bab=(section_judul or section_id or ''),
                    file_id=(bk_terpilih.file_id
                             if bk_terpilih is not None else None))
            # catat() SENGAJA tidak commit (desain modul 17Sep26) —
            # pemanggil yang commit, kalau tidak notifikasi hilang
            # saat request berakhir (akar terukur 26Sep26).
            db.commit()
        except Exception as e:                                 # noqa: BLE001
            log.warning('[pembimbing] notifikasi catatan baru gagal: %s', e)

        log.info('[pembimbing] catatan baru di bimbingan %s (bab %s, '
                 'sorotan %s, lampiran %s)', b.id, section_id,
                 'ada' if (teks_asli or '').strip() else '-', nama_disk or '-')
    return RedirectResponse(f'/tinjau/{token}', status_code=303)


@router.get('/tinjau/{token}/lampiran/{nama}')
def ambil_lampiran(token: str, nama: str, db: Session = Depends(get_db)):
    """Kirim satu lampiran — WAJIB lewat token yang masih hidup.

    ⚠️ Tidak ada jalur publik ke folder lampiran. Tanpa token yang sah,
    berkas TIDAK bisa diambil (kalau tautan dicabut → lampirannya ikut mati).
    ⚠️ Berkas dikirim APA ADANYA (tanpa eksekusi). Yang dilarang bukan
    membuka lampiran, tapi MENJALANKANNYA — dan itu tidak terjadi di sini.
    """
    b, sebab = P.cari_dari_token(db, token)
    if b is None:
        raise HTTPException(404, detail='Tautan tidak berlaku lagi.')
    p = LP.jalur(nama)
    if p is None:
        raise HTTPException(404, detail='Lampiran tidak ditemukan.')
    return FileResponse(p)


# ═══════════════════════════════════════════════════════════════════════
#  AKTIFKAN LAGI REVISI YANG DILEWATI — sisi PEMBIMBING
#  (Tahap 3.2, ACC Bos 24Sep26)
#
#  Aturan Bos verbatim:
#   "...Dan bisa aktif lagi jika pembimbing klik revisi (khusus untuk
#    revisi yang di lewati mahasiswa), jadi tetap Mahasiswa harus
#    melakukan revisi lagi dan tombol jadi aktif lagi di dashboard
#    mahasiswa."
#
#  ⚠️ HANYA lewat token pembimbing yang masih hidup (`cari_dari_token`).
#     Mahasiswa TIDAK punya jalan ke sini — itu yang menjaga aturan Bos.
# ═══════════════════════════════════════════════════════════════════════

@router.post('/tinjau/{token}/aktifkan')
def aktifkan(token: str, catatan_id: str = Form(''),
             db: Session = Depends(get_db)):
    """Pembimbing meminta ulang revisi yang dilewati mahasiswa."""
    b, sebab = P.cari_dari_token(db, token)
    if b is None:
        return RedirectResponse(f'/tinjau/{token}', status_code=303)

    try:
        cid = int(catatan_id)
    except (TypeError, ValueError):
        return RedirectResponse(f'/tinjau/{token}', status_code=303)

    #  ⚠️ WAJIB diperiksa: catatan itu harus MILIK bimbingan ini. Tanpa
    #  ini, pembimbing bisa mengaktifkan catatan mahasiswa lain hanya
    #  dengan menebak angka.
    from .models import CatatanPembimbing
    ada = (db.query(CatatanPembimbing)
           .filter(CatatanPembimbing.id == cid,
                   CatatanPembimbing.pembimbingan_id == b.id)
           .one_or_none())
    if ada is None:
        return RedirectResponse(f'/tinjau/{token}', status_code=303)

    berhasil, pesan = P.aktifkan_lagi(db, b.id, cid, ada.penulis_id)
    log.info('[pembimbing] aktifkan lagi catatan=%s hasil=%s pesan=%s',
             cid, berhasil, pesan)
    return RedirectResponse(f'/tinjau/{token}', status_code=303)
