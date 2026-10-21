"""app/catatan_ai.py — BUKU CATATAN AI (LANGKAH 2b-1, ACC Bos 16Sep26)

KENAPA ADA
==========
Arah Bos 16Sep26 (verbatim):
    "Atau AI kan selalu membaca dokumen terbaru / update. Nah ai mencatat
     bagian yang dia perbaiki atau istilahnya dia tandai sendiri selain dia
     baca seluruh naskah dokumen untuk dapat data terbaru, jadi ai masih dalam
     porsinya. Tidak perduli ada komentar pembimbing yang tidak dikerjakan
     mahasiswa atau ada komentar yang mahasiswa kerjakan sendiri. Ai hanya
     bekerja memperbaiki kalau di klik di komentar oleh user."

MASALAH YANG DIPECAHKAN
=======================
Uji 16Sep26 membuktikan: tabel `section_state` + `revisi_history` SUDAH ADA
(18 + 15 kolom) tapi **0 baris** — tidak ada kode yang menulis ke situ. Jadi:
  • AI tidak punya ingatan bagian mana yang sudah ia perbaiki
  • Dua komentar pada bab yang sama, dikerjakan terpisah → AI mengulang kerja
  • Mahasiswa tidak bisa melihat bagian mana yang sudah direvisi AI

APA YANG DICATAT (3 hal)
========================
  1. PER-BAGIAN (section_state) — tiap sub-bab/bab yang tersentuh revisi:
       isi_teks, char_count, sidik_bab (deteksi bab berubah), jenis_revisi,
       konteks_jenis (paragraf|sub_bab|bab|dokumen), sumber_terakhir ('ai'),
       diubah_pada
  2. RIWAYAT (revisi_history) — tiap kali AI bekerja:
       section_id, intent, komentar_dosen, ringkasan_perubahan,
       token_in/token_out/token_revisi/pengali, model_ai
  3. SIDIK BAB — hash isi bab; kalau isi berubah di luar jalur AI (mahasiswa
     edit manual) → sidik BEDA → ingatan dianggap basi → dibaca ulang.

ATURAN: TIDAK MENGGANGGU JALUR LAIN
===================================
  • Fungsi di sini HANYA menulis catatan; TIDAK mengubah naskah.
  • Kalau pencatatan gagal, revisi TETAP dianggap berhasil (jangan rugikan user
    karena kegagalan alat catat). Kegagalan dicatat ke log, bukan ke user.
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import FileBerkas, RevisiHistory, SectionState
from .parser import urai, pilih_pengali
from .state import buang_daftar_isi, petakan

log = logging.getLogger('eduai.catatan_ai')


def _peta_bersih(teks: str) -> list[dict]:
    """Peta bagian dari naskah yang SUDAH dibuang daftar isinya.

    🚨 BUG 16Sep26: memanggil `petakan()` langsung pada naskah mentah membuat
    DAFTAR ISI ikut terbaca sebagai bab palsu. Bukti pada disertasi S3 (402.252
    kar) — hasilnya 10 bagian: 5 bab palsu berukuran 701–12.817 kar (dari daftar
    isi) PLUS 5 bab sebenarnya (BAB I 13.978 kar … BAB IV 175.384 kar).
    Kalau catatan AI memakai bab palsu, "Buku Catatan AI" menandai bagian yang
    SALAH → AI berikutnya salah paham → naskah bisa rusak. WAJIB buang dulu.
    """
    if not teks:
        return []
    try:
        return petakan(buang_daftar_isi(teks))
    except Exception:                                        # noqa: BLE001
        return petakan(teks)


def _norm_section(s: str) -> str:
    """Normalkan nama bagian supaya bisa dibandingkan PERSIS.

    'BAB  III ' · 'bab iii' · 'Bab  Iii'  →  'BAB III'
    Spasi berlebih & besar-kecil diseragamkan; tanda baca pinggir dibuang.

    ⚠️ Dipakai untuk MENGHINDARI pencocokan substrat yang salah
    ('BAB I' in 'BAB III' = True). Kasus 04Okt26: revisi BAB II & III
    tercatat sebagai 'BAB I'.
    """
    t = re.sub(r'\s+', ' ', (s or '').strip()).strip(' :.-–—')
    return t.upper()


def _cocokkan_bagian(target: str, peta: list[dict]) -> dict | None:
    """Cari bagian di `peta` yang PALING TEPAT untuk `target`.

    URUTAN (04Okt26, ACC Bos Opsi B):
      1. COCOK PERSIS (dinormalkan spasi+kapital) — ini jalan utama.
      2. Kalau tidak ada: yang salah satu sisi memuat sisi lain SEBAGAI KATA
         UTUH, pilih yang TERPANJANG. Batas kata mencegah 'BAB I' cocok
         dengan 'BAB IX'.

    ⚠️ CACAT LAMA yang diperbaiki di sini: `sid in target` tanpa batas kata
    membuat 'BAB I' in 'BAB II' = True → revisi BAB II..IV semua tercatat
    sebagai BAB I (terbukti di produksi, naskah Asih file 81).

    Balas dict bagian, atau None kalau memang tidak ada yang cocok
    (JUJUR — jangan menebak bagian lain).
    """
    t = _norm_section(target)
    if not t:
        return None
    for b in peta:
        if _norm_section(str(b.get('section_id') or '')) == t:
            return b
    kandidat = []
    for b in peta:
        s = _norm_section(str(b.get('section_id') or ''))
        if not s:
            continue
        if t in s or s in t:
            pendek, panjang = (t, s) if len(t) <= len(s) else (s, t)
            i = panjang.find(pendek)
            while i >= 0:
                lanjut = panjang[i + len(pendek):i + len(pendek) + 1]
                if lanjut in ('', ' ', '.', ':', '-', '–'):
                    kandidat.append((len(s), b))
                    break
                i = panjang.find(pendek, i + 1)
    if kandidat:
        kandidat.sort(key=lambda kv: kv[0], reverse=True)
        return kandidat[0][1]
    return None


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def sidik_isi(teks: str) -> str:
    """Sidik jari isi bab — 16 huruf pertama sha256 dari teks yang dirapikan.

    Dipakai mendeteksi: apakah isi bab berubah TANPA lewat jalur AI
    (mis. mahasiswa mengedit manual di OnlyOffice).
    """
    t = (teks or '').strip()
    if not t:
        return ''
    t = ' '.join(t.split())          # abaikan spasi/baris berlebih
    return hashlib.sha256(t.encode('utf-8', 'ignore')).hexdigest()[:16]


def bagian_tersentuh(peta: list[dict], posisi: int) -> dict | None:
    """Cari bagian (bab/sub-bab) yang memuat `posisi` karakter dalam naskah."""
    kandidat = None
    for i, b in enumerate(peta):
        awal = b.get('mulai', 0)
        akhir = (peta[i + 1].get('mulai', 10 ** 12)
                 if i + 1 < len(peta) else 10 ** 12)
        if awal <= posisi < akhir:
            kandidat = b
            break
    return kandidat


def _isi_tanpa_judul(teks: str) -> str:
    """Buang baris judul di awal teks (mis. '1.2 Rumusan Masalah').

    Dipakai sebagai CADANGAN kalau bagian tak ditemukan di peta — supaya
    isi yang dihitung/di-sidik tidak ikut memuat judul bagiannya (konsisten
    dengan `isi_teks` yang dikeluarkan `petakan()`).

    Aman: kalau baris pertama pendek & berisi nomor/angka, buang; kalau tidak,
    teks dikembalikan utuh. Tidak pernah melempar exception.
    """
    try:
        teks = (teks or '').lstrip()
        if not teks:
            return ''
        baris, _, sisa = teks.partition('\n')
        # Hanya buang kalau baris pertama MIRIP JUDUL: pendek + ada nomor.
        if (len(baris) <= 120 and sisa.strip()
                and re.search(r'\d', baris) and len(baris) < len(teks) * 0.5):
            return sisa.lstrip()
        return teks
    except Exception:                                     # noqa: BLE001
        return teks or ''


def catat_revisi(
    db: Session,
    *,
    user_id: int,
    file_id: int | None,
    bab: str,
    komentar: str,
    naskah_sebelum: str,
    naskah_sesudah: str,
    model: str = '',
    token_in: int = 0,
    token_out: int = 0,
    token_revisi: int = 0,
    konteks: str = '',
) -> dict:
    """Tulis catatan revisi AI ke `section_state` + `revisi_history`.

    Mengembalikan ringkasan yang bisa dipakai pemanggil (untuk log/UI).
    TIDAK melempar exception — kegagalan catat hanya dicatat ke log.
    """
    hasil = {'dicatat': False, 'section_id': '', 'intent': '', 'alasan': ''}
    #  🚨 GERBANG ANTI-BUG (17Sep26): `komentar` WAJIB STRING.
    #     AKAR BUG: pemanggil mengirim LIST[str] → `urai()` meledak
    #     (`'list' object has no attribute 'strip'`) → exception ditelan
    #     `except` di bawah → ingatan dokumen KOSONG tanpa jejak
    #     (section_state=0, revisi_history=0 padahal versi_dokumen bertambah).
    #     Lebih baik TERIAK di sini daripada gagal senyap di runtime.
    if not isinstance(komentar, str):
        if isinstance(komentar, (list, tuple)):
            komentar = '\n'.join(str(k).strip() for k in komentar if k)
        else:
            raise TypeError(
                'catat_revisi(komentar=...) WAJIB str, bukan '
                f'{type(komentar).__name__}. Pemanggil harus menggabung '
                'list komentar jadi satu teks (lihat baris_komentar di ai.py).')
    try:
        # ── 1) Tentukan bagian mana yang tersentuh ─────────────────────────
        #  🚨 CACAT ke-21 & ke-22 (ACC Bos 24Sep26 — "pondasi harus kuat"):
        #     Dulu peta dibuat dari `naskah_sesudah` (= hasil revisi AI).
        #     Akibat terukur pada tesis Bos:
        #       • `section_title` tersimpan KOSONG — draf AI tidak memuat
        #         judul "Rumusan Masalah", jadi `section_title` = '' → ingatan
        #         tidak menyebut bagian apa yang dikerjakan.
        #       • `char_count` SALAH = 4.000 padahal bagian asli 367 kar —
        #         karena menghitung ukuran DRAF AI, bukan ukuran bagian asli.
        #     Yang BENAR: cari JUDUL & UKURAN dari `naskah_sebelum` (naskah
        #     asli yang dikirim), lalu fallback ke `naskah_sesudah` kalau
        #     sebelum kosong (mis. pemanggil lama).
        _sumber_cari = naskah_sebelum or naskah_sesudah or ''
        peta = _peta_bersih(_sumber_cari)
        section_id = bab or ''
        section_title = ''
        kategori = 'bab'

        if not section_id or section_id == '__seluruh__':
            # Peta dari naskah baru → ambil ikhtisar semua bagian
            section_id = '__seluruh__'
            section_title = 'Seluruh dokumen'
            kategori = 'dokumen'
        else:
            #  🚨 CACAT PRODUKSI (04Okt26, ACC Bos Opsi B) — pencocokan LAMA:
            #       if sid == section_id or sid in section_id or section_id in sid
            #     `sid in section_id` bikin substrat cocok salah:
            #       minta 'BAB II'  → 'BAB I'  in 'BAB II'  = True → dapat BAB I
            #       minta 'BAB III' → 'BAB I'  in 'BAB III' = True → dapat BAB I
            #       minta 'BAB IV'  → 'BAB I'  in 'BAB IV'  = True → dapat BAB I
            #     Akibat terukur di produksi (naskah Asih file 81):
            #       revisi BAB II & III TERCATAT sebagai 'BAB I'
            #       ⇒ section_state salah bab → Mode Belajar terkunci
            #       ⇒ Buku Catatan AI menempel ke bab yang salah
            #     ATURAN BARU: COCOK PERSIS dulu (dinormalkan spasi+kapital).
            #     Kalau tidak ada yang persis → ambil yang PALING COCOK
            #     (yang salah satu sisi memuat sisi lain) dan terpanjang,
            #     BUKAN yang pertama ketemu.
            _pas = _cocokkan_bagian(section_id, peta)
            if _pas is not None:
                section_title = str(_pas.get('section_title') or '')
                kategori = str(_pas.get('kategori') or 'bab')
                section_id = str(_pas.get('section_id') or section_id)

        # ── 2) Urai komentar → intent & pengali (Rp 0, tanpa AI) ───────────
        #    `urai()` mengembalikan DICT; `pilih_pengali()` menerima STRING intent.
        try:
            u = urai(komentar or '')
            intent = (u.get('intent') or '') if isinstance(u, dict) else ''
            pengali = pilih_pengali(intent, komentar or '') if intent else 1
        except Exception:                                    # noqa: BLE001
            intent, pengali = '', 1

        # ── 3) Ambil isi bagian yang tersentuh (untuk sidik jari & ukuran) ─
        #  ⚠️ CACAT ke-22: `char_count` = 4.000 padahal bagian asli 367 kar
        #     (terukur 24Sep26). Sebab: `peta` lama dibuat dari HASIL revisi,
        #     jadi `isi_teks` = draf AI (dipotong 4.000) — bukan bagian asli.
        #     Sekarang `peta` dibuat dari `naskah_sebelum`, jadi `isi_teks`
        #     = isi bagian SEBELUM revisi → `char_count` = ukuran ASLI.
        #     `sidik_bab` juga jadi sidik isi SEBELUM — itu yang diinginkan:
        #     deteksi "user sudah mengubah bagian ini sejak terakhir".
        isi = ''
        if section_id != '__seluruh__':
            for b in peta:
                sid = str(b.get('section_id') or '')
                if sid == section_id:
                    isi = str(b.get('isi_teks') or '')
                    break
        if not isi:
            # Fallback: buang judul baris pertama supaya konsisten dgn peta.
            isi = _isi_tanpa_judul(naskah_sebelum or naskah_sesudah or '')

        # ── 4) Tulis/timpa section_state ───────────────────────────────────
        if file_id:
            baris = db.scalars(
                select(SectionState).where(
                    SectionState.file_id == file_id,
                    SectionState.section_id == section_id,
                )
            ).first()
            if baris is None:
                baris = SectionState(
                    file_id=file_id, user_id=user_id, section_id=section_id)
                db.add(baris)
                baris.versi = 1
            else:
                baris.versi = (baris.versi or 1) + 1

            baris.section_title = section_title or baris.section_title or ''
            baris.kategori = kategori or baris.kategori or 'bab'
            baris.isi_teks = isi[:200_000]
            baris.char_count = len(isi)
            baris.sidik_bab = sidik_isi(isi)
            baris.jenis_revisi = intent or baris.jenis_revisi or ''
            baris.konteks_jenis = konteks or baris.konteks_jenis or ''
            baris.sumber_terakhir = 'ai'          # ← AI menandai dirinya sendiri
            baris.diubah_pada = _now()

        # ── 5) Tulis revisi_history ────────────────────────────────────────
        if file_id:
            penggal = (naskah_sesudah or '')[:1500]
            ringkas = (f'Revisi {intent or "REVISI"} pada {section_id}: '
                       f'{len(naskah_sebelum or ""):,} → '
                       f'{len(naskah_sesudah or ""):,} karakter')
            db.add(RevisiHistory(
                file_id=file_id, user_id=user_id,
                section_id=section_id,
                versi=1,
                intent=intent,
                komentar_dosen=(komentar or '')[:4000],
                ringkasan_perubahan=ringkas,
                diff_summary=penggal,
                token_in=int(token_in or 0),
                token_out=int(token_out or 0),
                token_revisi=int(token_revisi or 0),
                pengali=int(pengali or 1),
                model_ai=model or '',
            ))

        db.commit()
        hasil.update(dicatat=True, section_id=section_id, intent=intent)
        log.info('[catatan_ai] revisi dicatat: file=%s bagian=%s intent=%s '
                 'pengali=%s model=%s', file_id, section_id, intent,
                 pengali, model or '-')
    except Exception as e:                                   # noqa: BLE001
        # JANGAN gagalkan revisi hanya karena catatan gagal (user tidak boleh
        # dirugikan). Cukup catat di log untuk ditelusuri.
        try:
            db.rollback()
        except Exception:                                    # noqa: BLE001
            pass
        hasil['alasan'] = f'{type(e).__name__}: {e}'
        log.warning('[catatan_ai] GAGAL mencatat (revisi tetap dianggap sukses): %s',
                    hasil['alasan'])
    return hasil


def bab_yang_sudah_direvisi(db: Session, file_id: int) -> list[dict]:
    """Bagian mana yang sudah pernah direvisi AI (untuk 'Buku Catatan')."""
    if not file_id:
        return []
    baris = db.scalars(
        select(SectionState).where(SectionState.file_id == file_id)
    ).all()
    return [
        {
            'section_id': b.section_id,
            'judul': b.section_title,
            'char_count': b.char_count,
            'jenis_revisi': b.jenis_revisi,
            'konteks': b.konteks_jenis,
            'sumber': b.sumber_terakhir,
            'diubah_pada': b.diubah_pada.isoformat() if b.diubah_pada else '',
            'sidik': b.sidik_bab,
        }
        for b in baris
    ]


def ringkasan_untuk_ai(db: Session, file_id: int, batas: int = 12) -> str:
    """Ringkasan untuk DISISIPKAN KE PROMPT — supaya AI tahu apa yang sudah
    ia kerjakan, tidak mengulang, dan tidak bertentangan dengan revisinya sendiri.
    """
    baris = bab_yang_sudah_direvisi(db, file_id)
    if not baris:
        return ''
    potong = baris[-batas:]
    garis = [f'- {b["section_id"]} {b["judul"]} — {b["jenis_revisi"]}'
             f' ({b["char_count"]:,} kar, {b["diubah_pada"][:16]})'
             for b in potong]
    return (
        'CATATAN REVISI SEBELUMNYA (yang SUDAH dikerjakan AI pada dokumen ini). '
        'JANGAN mengulang pekerjaan yang sama; jaga agar tidak bertentangan '
        'dengan hasil sebelumnya:\n' + '\n'.join(garis)
    )
