"""Section State — ingatan per sub-bab naskah.

=== SALINAN POLA DARI PENELITIAN-BOT (SUMBER READ-ONLY) ===
Asal: /opt/data/services/penelitian-bot/telegram-bot/helpers/section-state.js
      baris 5-13   -> CATEGORY_MAP        (26 sub-bab -> bab1..bab5/meta/lampiran)
      baris 15-21  -> getCategoryFor()
      baris 23-40  -> initSectionState()
      baris 160-190 -> HEADING_PATTERN + SECTION_TITLE_LOOKUP
      baris 195-230 -> parseSectionsFromBlocks()

KENAPA DIBUAT: supaya AI ingat APA yang sudah ditulis/direvisi per sub-bab.
Tanpa ini, AI merevisi 1.1 tanpa tahu 1.2 sudah dibahas -> tumpang tindih.
Dan tanpa ini, KUOTA tidak bisa dihitung (deteksi bab = penentu harga).

ADAPTASI (jangan copy buta):
  - `blocks` (Array of {type,text}) -> EduAi pakai daftar bab dari docx
    (nama bab + isi teks), bukan blok terstruktur.
  - `prisma.sectionState` -> tabel `section_state` di models.py.
  - `wordCount` -> `char_count` (EduAi menghitung KARAKTER, sesuai tarif
    Token Revisi yang dihitung dari karakter/token — MASTER_PLAN §4.13).
"""

from __future__ import annotations

import logging
import re
from typing import Any

log = logging.getLogger(__name__)

# ── CATEGORY_MAP — section-state.js baris 5-13 ──────────────────────────
CATEGORY_MAP: dict[str, str] = {
    # meta
    'judul': 'meta', 'abstrak': 'meta', 'kata_pengantar': 'meta',
    'daftar_pustaka': 'meta', 'daftar_isi': 'meta', 'daftar_tabel': 'meta',
    'daftar_gambar': 'meta', 'daftar_lampiran': 'meta',
    # BAB I
    '1.1': 'bab1', '1.2': 'bab1', '1.3': 'bab1', '1.4': 'bab1', '1.5': 'bab1',
    # BAB II
    '2.1': 'bab2', '2.2': 'bab2', '2.3': 'bab2', '2.4': 'bab2',
    # BAB III
    '3.1': 'bab3', '3.2': 'bab3', '3.3': 'bab3', '3.4': 'bab3', '3.5': 'bab3',
    # BAB IV
    '4.1': 'bab4', '4.2': 'bab4', '4.3': 'bab4', '4.4': 'bab4', '4.5': 'bab4',
    # BAB V
    '5.1': 'bab5', '5.2': 'bab5', '5.3': 'bab5', '5.4': 'bab5',
    # lampiran
    'lampiran': 'lampiran', 'lampiran_kuesioner': 'lampiran',
    'lampiran_pedoman': 'lampiran', 'lampiran_transkrip': 'lampiran',
}

# ── SECTION_TITLE_LOOKUP — section-state.js baris 165-187 ───────────────
SECTION_TITLE_LOOKUP: dict[str, str] = {
    '1.1': 'Latar Belakang',
    '1.2': 'Rumusan Masalah',
    '1.3': 'Tujuan Penelitian',
    '1.4': 'Manfaat Penelitian',
    '1.5': 'Sistematika Penulisan',
    '2.1': 'Landasan Teori',
    '2.2': 'Penelitian Terdahulu',
    '2.3': 'Kerangka Berpikir',
    '2.4': 'Hipotesis',
    '3.1': 'Metode Penelitian',
    '3.2': 'Populasi dan Sampel',
    '3.3': 'Instrumen Penelitian',
    '3.4': 'Teknik Analisis Data',
    '3.5': 'Definisi Operasional Variabel',
    '4.1': 'Deskripsi Responden',
    '4.2': 'Uji Instrumen',
    '4.3': 'Uji Asumsi Klasik',
    '4.4': 'Uji Hipotesis',
    '4.5': 'Pembahasan',
    '5.1': 'Kesimpulan',
    '5.2': 'Saran',
    '5.3': 'Keterbatasan Penelitian',
}

# ── HEADING_PATTERN — section-state.js baris 164 ────────────────────────
# Nomor sub-bab (1.1 / A.1), judul BAB (BAB I / BAB IV), atau LAMPIRAN.
HEADING_PATTERN = re.compile(
    r'^(?:\d+\.\d+|[A-Z]\.\d+|BAB\s+[IVX]+|LAMPIRAN)', re.IGNORECASE)

# ── Penanda DAFTAR ISI / DAFTAR TABEL / DAFTAR GAMBAR ───────────────────
# KENAPA PENTING: pada naskah nyata (tesis Bos, 15Sep26), DAFTAR ISI memuat
# baris seperti "1.1 Latar Belakang ....... 1" yang IKUT terdeteksi sebagai
# sub-bab — panjangnya cuma 30 karakter, padahal isi asli 13.523 karakter.
# Akibatnya peta bab salah -> harga Token Revisi salah. WAJIB dibuang dulu.
_PENANDA_DAFTAR = re.compile(
    r'^\s*(DAFTAR\s+ISI|DAFTAR\s+TABEL|DAFTAR\s+GAMBAR|DAFTAR\s+LAMPIRAN|'
    r'TABLE\s+OF\s+CONTENTS|DAFTAR\s+PUSTAKA|HALAMAN\s+JUDUL|'
    r'LEMBAR\s+PENGESAHAN|LEMBAR\s+PERSETUJUAN|ABSTRAK|ABSTRACT)\s*$',
    re.IGNORECASE | re.MULTILINE)

# Baris daftar isi punya titik-titik pengarah: "1.1 Latar Belakang ...... 3"
_POLA_BARIS_DAFTAR = re.compile(r'\.{3,}\s*\d*\s*$|\.{5,}', re.MULTILINE)

# 🔴 BUG ke-14 (16Sep26, skripsi S1 Olahraga UNHAS): DAFTAR ISI dengan nama
# sub-bab PANJANG membungkus jadi DUA baris, dan nomor halaman menempel di
# ujung baris KEDUA (tanpa titik pengarah):
#     "4.1 Data Distribusi Usia, Usia Pertama Haid, Tinggi badan, dan Berat Badan"
#     "Atlet Kriket Pra PON 2021 yang Melakukan Latihan di KONI Sulawesi Selatan37"
#     "4.2 Data Distribusi Tingkat Aktivitas Fisik Atlet Kriket pra PON 2021 yang"
#     "Melakukan Latihan di KONI Sulawesi Selatan ..............................................38"
# Baris ke-2 ("...Selatan37") TIDAK cocok pola titik-pengarah maupun pola
# menempel biasa → daftar isi LOLOS → jadi sub-bab palsu 295 kar.
# Aturan: baris yang diakhiri NOMOR HALAMAN menempel (tanpa spasi/titik) ATAU
# baris yang dibuka nomor sub-bab dan diakhiri nomor = baris daftar isi.
_POLA_BARIS_DAFTAR_HAL = re.compile(r'\d{1,4}\s*$')

# 🔴 BUG NYATA (ditemukan 16Sep26 pada skripsi S1 nyata UNMUL):
# Di banyak naskah, DAFTAR ISI tidak memakai titik-titik pengarah, tapi
# nomor halaman MENEMPEL langsung ke judul, contoh baris aslinya:
#     "BAB I PENDAHULUAN1"
#     "1.1Latar Belakang1"
#     "BAB II TINJAUAN PUSTAKA5"
# Akibatnya _POLA_BARIS_DAFTAR tidak menangkapnya, daftar isi LOLOS, dan
# kode memakai daftar isi sebagai ISI BAB → peta rusak: section_id kosong
# dan satu bab menelan seluruh naskah (BAB V = 59.671 kar dari 65.932 kar).
# Pola ini menangkap baris daftar isi bergaya "judul nempel nomor halaman".
_POLA_BARIS_DAFTAR_NEMPEL = re.compile(
    r'^(?:BAB\s+[IVX]+\s*[A-Z][A-Z\s,&\-]{3,}|'
    r'\d+\.\d+(?:\.\d+)*\s*[A-Z][^\n]{2,})\d{1,3}\s*$',
    re.MULTILINE)

# 🔴 BUG NYATA ke-3 (16Sep26, skripsi S1 Kedokteran UNHAS): blok DAFTAR TABEL /
# DAFTAR GAMBAR berisi baris seperti
#     "4.1 Data Distribusi Usia, Usia Pertama Haid, Tinggi badan, dan Berat Badan"
#     "Table 4.1 Data Distribusi Usia, ..."
#     "Gambar 2.1 Kerangka Berpikir"
# Baris-baris ini LOLOS dari penyaring lain (tanpa titik pengarah, judul wajar),
# lalu dianggap JUDUL SUB-BAB. Akibatnya sub-bab 4.1/5.1 "isinya" cuma 74–81
# karakter (sisa baris daftar), padahal isi aslinya ribuan karakter.
_POLA_BARIS_DAFTAR_TABEL = re.compile(
    r'^\s*(?:Table|Tabel|Gambar|Grafik|Diagram|Lampiran)\s*\d+(?:\.\d+)*\s+\S',
    re.IGNORECASE)

# 🔴 BUG NYATA ke-5 (16Sep26, tesis Bos): baris DAFTAR GAMBAR/TABEL dengan
# nomor halaman MENEMPEL dan judul langsung nempel ke nomornya, contoh asli:
#     "Gambar 1.2Proyeksi Pendapatan Pasar Logistik Indonesia 2020–2029 4"
#     "1.1Nilai PDB Pergudangan, Jasa Penunjang Angkutan, Pos dan Kurir 3"
# Baris ini lolos dari semua penyaring sebelumnya, lalu TERBACA sebagai
# sub-bab "1.1" berisi cuma 95 karakter — padahal isi asli 1.1 = 12.044 kar.
# Ini menyangkut HARGA (kuota revisi dihitung dari panjang bagian), jadi wajib
# disaring. Ciri: diakhiri nomor halaman 1–3 digit, dan angka di akhir BUKAN
# bagian tahun/rentang (mis. "2020–2029" tidak dianggap nomor halaman).
_POLA_BARIS_DAFTAR_GAMBAR_NEMPEL = re.compile(
    r'^\s*(?:(?:Gambar|Tabel|Table|Grafik|Diagram|Lampiran)\s*\d+(?:\.\d+)*|'
    r'\d+\.\d+)\s*\S[^\n]{2,}\s\d{1,3}\s*$',
    re.MULTILINE)

# Judul bab besar di naskah utuh: "BAB 1 PENDAHULUAN" / "BAB I PENDAHULUAN"
_POLA_JUDUL_BAB = re.compile(
    r'^\s*BAB\s+([IVX]+|\d+)\s*$', re.IGNORECASE | re.MULTILINE)


def kategori_bab_besar(nomor: str | None) -> str:
    """Kategori untuk BAB BESAR ('BAB I'..'BAB V') → 'bab1'..'bab5'.

    🚨 AKAR CACAT DITEMUKAN 05Okt26 (temuan uji satpam [9] & [71]):
       `deteksi_bab_besar` menulis kategori HARFIAH `'bab'`, sedangkan
       `deteksi_subbab` menulis `'bab1'..'bab5'` (lewat get_category_for).
       Akibatnya naskah yang dipetakan per BAB besar (karena sub-bab < 3)
       TIDAK PERNAH terbuka di Mode Belajar — `belajar.py` mencari
       'bab1'..'bab5', bukan 'bab'.
       Inilah cacat yang Wulan tambal berulang di konsumen; kini
       DIPERBAIKI DI AKARNYA: penulis kategori menghasilkan bentuk yang sama.

    Aman: nomor tak dikenal → 'bab' (perilaku lama, tidak melempar galat).
    """
    if not nomor:
        return 'bab'
    angka = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
             'VI': 6, 'VII': 7, 'VIII': 8}.get(
        str(nomor).strip().upper().replace('BAB', '').strip())
    if angka is None:
        # nomor berupa angka arab ('1'..'8')
        sisa = str(nomor).strip().upper().replace('BAB', '').strip()
        angka = int(sisa) if sisa.isdigit() else None
    if angka and 1 <= angka <= 5:
        return f'bab{angka}'
    return 'bab'          # di luar 1..5 → perilaku lama


def get_category_for(section_id: str | None) -> str:
    """section-state.js getCategoryFor() baris 15-21.

    Default 'bab' kalau tidak dikenal — JANGAN lempar galat.
    """
    if not section_id:
        return 'bab'
    sid = section_id.strip().lower().replace(' ', '_')
    if sid.startswith('lampiran'):
        return 'lampiran'
    if sid in ('judul', 'abstrak', 'kata_pengantar', 'daftar_pustaka',
               'daftar_isi', 'daftar_tabel', 'daftar_gambar', 'daftar_lampiran'):
        return 'meta'
    # ⭐ 05Okt26: 'BAB I'..'BAB V' (bab besar) juga diarahkan ke bab1..bab5,
    #    supaya penulis kategori tunggal — tidak lagi dua bentuk.
    if re.match(r'^bab\s+[ivx\d]+\b', section_id.strip(), re.IGNORECASE):
        return kategori_bab_besar(section_id)
    return CATEGORY_MAP.get(sid, 'bab')


def title_for(section_id: str, default: str = '') -> str:
    """Judul baku sub-bab. Kosong kalau tidak ada di peta (pakai judul dokumen)."""
    return SECTION_TITLE_LOOKUP.get((section_id or '').strip(), default)


def semua_section_id() -> list[str]:
    """Daftar seluruh id sub-bab yang dikenal (untuk validasi / tampilan)."""
    return list(SECTION_TITLE_LOOKUP.keys())


# ═══════════════════════════════════════════════════════════════════════
#  DETEKSI SUB-BAB DARI TEKS NASKAH
# ═══════════════════════════════════════════════════════════════════════

# 🔴 BUG NYATA (ditemukan 16Sep26 pada skripsi S1 nyata UNMUL):
# Sebelumnya pola ini WAJIB punya spasi setelah nomor bab:
#     "BAB I"  ✓   "BAB I PENDAHULUAN"  ✓   "BAB IPENDAHULUAN"  ✗ GAGAL
# Naskah nyata SANGAT sering menempelkan judul tanpa spasi ("BAB IPENDAHULUAN",
# "BAB IIIMETODOLOGI PENELITIAN") — hasil ekspor Word/Docs. Akibatnya 0 bab
# terdeteksi → peta jatuh ke '__seluruh__' (seluruh naskah jadi 1 unit) →
# kuota revisi salah dan AI kehilangan peta bab.
# Kini menerima ketiganya. Nomor bab dibatasi angka romawi 1–4 huruf (I–XXIV)
# supaya kata berawalan "BAB..." lain tidak ikut tertangkap.
# 🔴 BUG NYATA ke-7 (16Sep26, disertasi S3 323 hal): pola lama memakai
# re.IGNORECASE sehingga kalimat biasa
#     "bab ini akan menyajikan determinan yang memengaruhi terjadinya ..."
# dibaca sebagai JUDUL BAB dan menelan 126.225 kar (seluruh isi BAB IV) —
# peta jadi punya dua "BAB I".
# PERBAIKAN: kata "BAB" tetap case-insensitive (naskah nyata menulis "Bab"),
# tapi NOMOR ROMAWI wajib HURUF BESAR. "bab ini" → ditolak ("ini" bukan angka
# romawi); "BAB I" / "Bab II" → diterima.
# ⭐ 05Okt26 (putusan Bos "A") — TAMBAH 2 BENTUK YANG NYATA ADA DI NASKAH BOS:
#   (a) BAB ANGKA ARAB — "BAB 1 PENDAHULUAN" ... "BAB 6 KESIMPULAN".
#       Bukti: 290465463.pdf → mesin BAB=0, padahal "BAB 1..6" ditulis 8 kali
#       (Jev melihat 3 bab, mesin 0 → Jev benar, mesin buta).
#       CATATAN: app/belajar.py:301 SUDAH menerima angka Arab sejak lama —
#       hanya state.py (jalur peta+HARGA) yang tertinggal. Pola kembar!
#   (b) ROMAWI TITIK TANPA KATA "BAB" — "IV. HASIL DAN PEMBAHASAN".
#       Bukti: 290462754.pdf → mesin BAB=0, naskah menulis "IV." & "V.".
#       Terukur aman: 18 naskah → 2 bab tertangkap, 0 sampah.
# 🚨 JEBAKAN '\r' (PDF): WAJIB pakai `[ \t]*(.*)` (bukan `$` telanjang).
_POLA_BAB = re.compile(
    r'^[ \t]*(?i:BAB)[ \t]+([IVXLC]{1,5}|\d{1,2})[ \t]*(.*)$',
    re.MULTILINE,
)
#  romawi + TITIK, tanpa kata "BAB" — grup 1 = nomor, grup 2 = judul
#  🚨 WAJIB `[ \t\r]*$`: PDF menulis 'IV. HASIL DAN PEMBAHASAN \r'
#     (spasi + \r). `$` Python cocok SEBELUM '\n', BUKAN sebelum '\r'
#     → tanpa ini polanya DIAM-DIAM tidak cocok (nyaris lolos ke produksi).
_POLA_BAB_TITIK = re.compile(
    r'^[ \t]*([IVXLC]{1,5})\.[ \t]+([A-Z][A-Z0-9 ,\-]{3,70})[ \t\r]*$',
    re.MULTILINE,
)


# Baris sampah: hanya angka / angka romawi kecil / tanda baca.
_POLA_BARIS_SAMPAH = re.compile(r'^[\d\.\-\)\s]*$|^[ivxlcdm]{1,5}\.$', re.IGNORECASE)


def _judul_dari_baris_berikut(teks: str, pos_akhir: int) -> str:
    """Ambil judul BAB dari baris berikutnya bila baris "BAB I" berdiri sendiri.

    🔴 BUG NYATA ke-9 (16Sep26, disertasi S3 & skripsi UNMUL): naskah nyata
    sering menulis judul bab di baris TERPISAH:
        BAB I
        PENDAHULUAN
    Versi sebelumnya hanya melihat baris yang sama → judul kosong → semua bab
    berjudul "BAB I". Sekarang lihat 2 baris berikutnya, lewati baris kosong
    dan baris sampah (nomor halaman "1." / "ix").
    """
    for baris in teks[pos_akhir:pos_akhir + 300].split('\n')[1:4]:
        b = baris.strip()
        if not b:
            continue
        if _POLA_BARIS_SAMPAH.match(b):     # "1." / "ix" / "..." → sampah
            continue
        if len(b) > 90:                     # terlalu panjang → bukan judul
            return ''
        j = re.sub(r'\s+\d{1,3}\s*$', '', b).strip()   # buang nomor halaman
        return j if len(j) >= 3 else ''
    return ''
# 🔴 BUG NYATA (ditemukan 16Sep26 pada skripsi S1 Kedokteran UNHAS):
# Pola lama `^\s*(\d+\.\d+)\s+(.{0,120})$` menerima SEMUA "angka.angka",
# sehingga kalimat statistik ikut jadi "sub-bab", contoh nyata:
#     "8.28 kg. The highest distribution of menstrual cycles was ..."
#     → terbaca sebagai sub-bab "8.28" dengan judul "kg. The highest ...".
# Akibatnya peta rusak: muncul section_id palsu, dan nomor asli (4.1, 5.1)
# justru menangkap DAFTAR TABEL (isi 69–151 kar) bukan isi aslinya
# (padahal isi asli bab itu 15.623 kar).
#
# CIRI JUDUL SUB-BAB SUNGGUHAN (dipakai untuk menyaring):
#   (a) nomor wajar: bab 1–29, anak 0–29 → "2.1", "4.12", bukan "8.28"
#   (b) judul diawali HURUF BESAR (kalimat statistik diawali huruf kecil)
#   (c) TIDAK diakhiri titik-titik daftar isi
#   (d) judul bukan potongan kalimat (tanpa pola "kg." / satuan di awal)
#
# 🔴 BUG NYATA ke-17 (24Sep26, ACC Bos) — GAYA "1.1." BERTITIK DUA TIDAK DIKENALI.
# Pola lama menuntut SPASI LANGSUNG setelah anak nomor:
#       ^\s*([1-9]|[12]\d)\.(\d{1,2})\s+([A-Z][^\n]{2,110})$      ← lama
# Naskah nyata banyak menulis "1.1. Latar Belakang" (titik KEDUA). Akibatnya
# SELURUH sub-bab hilang SENYAP (tanpa galat), peta jatuh ke BAB BESAR.
# Terukur pada 5 dokumen contoh (24Sep26, sebelum → sesudah):
#       tesis S2 manajemen   : 0 → 6 sub-bab   (20 baris "1.1." tadinya buta)
#       tesis S2 pend.bahasa : 0 → 0           (memang TANPA nomor sub-bab)
#       tesis S2 sastra      : 0 → 0           (memang TANPA nomor sub-bab)
#       skripsi S1 UNMUL     : 0 → 0           (memang TANPA nomor sub-bab)
#       skripsi S1 olahraga  : 5 → 5           (sudah jalan, tidak rusak)
# → Titik kedua kini OPSIONAL (`.?`). PERUBAHAN 1 KARAKTER, tanpa efek samping:
#   naskah bergaya "1.1 " tetap dikenali seperti sebelumnya.
# CATATAN JUJUR: 3 dari 5 dokumen memang TIDAK menomori sub-bab sama sekali,
# jadi perbaikan ini HANYA menolong naskah bergaya bernomor. Sisanya perlu
# pendekatan lain (belum diputuskan Bos).
_POLA_SUBBAB = re.compile(
    r'^\s*([1-9]|[12]\d)\.(\d{1,2})\.?\s+'
    r'([A-Z][^\n]{2,110})$',
    re.MULTILINE,
)

#  ⭐ 05Okt26 (putusan Bos "A"): naskah yang sub-babnya HURUF — "A. Latar
#     Belakang". Nyata di 290460818.pdf & 389360758.pdf (mesin sub-bab=0).
#     TERUKUR AMAN: 43 judul bagian nyata, 0 sampah, 0 dari daftar pustaka.
#  🚫 pola "1) angka tutup" SENGAJA TIDAK dipakai — terukur MENANGKAP RUMUS
#     & kalimat ("1. Skor minimum : ...", "1. Pajak merupakan kontribusi…")
#     → jadi sub-bab palsu → HARGA SALAH. Bukti: _sketsa/ukur_pola_huruf_angka.py.
#  ⚠️ Dipakai HANYA kalau pola x.y tidak menemukan apa pun (perilaku lama utuh).
_POLA_SUBBAB_HURUF = re.compile(
    r'^[ \t]*([A-Z])\.\t?[ \t]+([A-Z][^\n]{3,70})[ \t\r]*$',
    re.MULTILINE,
)


def _subbab_palsu(nomor: str, judul: str, baris_penuh: str) -> bool:
    """Saring kandidat sub-bab yang sebenarnya BUKAN judul sub-bab.

    Dipakai agar kalimat statistik / daftar tabel tidak dianggap sub-bab.
    """
    j = (judul or '').strip()

    # (a) judul harus diawali huruf besar & minimal 3 huruf (bukan "kg." dst.)
    if not re.match(r'^[A-Z][a-z]{2,}', j):
        return True

    # (b) potongan kalimat: ada satuan/angka menempel di awal judul
    if re.match(r'^(?:kg|cm|mm|km|ml|gr|gram|tahun|orang|responden|%)\b',
                j, re.IGNORECASE):
        return True

    # (c) kalimat berlanjut: judul diakhiri koma / kata sambung → potongan
    if re.search(r'[,;]$', j) or re.search(
            r'\b(?:dan|atau|yang|untuk|dengan|pada|dari|di|ke)$', j, re.IGNORECASE):
        return True

    # (d) baris terlalu panjang → kemungkinan paragraf, bukan judul
    if len(baris_penuh.strip()) > 130:
        return True

    return False


def _baris_setelahnya(teks: str, pos: int) -> str | None:
    """Baris PERTAMA setelah `pos` yang tidak kosong (None kalau tidak ada)."""
    if pos >= len(teks):
        return None
    for b in teks[pos:].split('\n'):
        b_str = b.strip()
        if b_str:
            return b_str
    return None


def _masih_isi_daftar(baris: str) -> bool:
    """Apakah baris ini masih bagian DAFTAR ISI (bukan isi naskah asli)?

    Dipakai membedakan "BAB I" di daftar isi vs "BAB I" judul bab sungguhan.
    🔴 BUG ke-11 (16Sep26): disertasi S3 punya DAFTAR ISI KEDUA yang isinya
    hanya nomor/romawi pendek sehingga tidak ada titik-pengarah untuk dibuang.

    Tanda masih daftar isi:
      • nomor/romawi pendek:  "1." "2." "ix" "xi" "F." "I." "a." "1" "B."
      • baris judul pendek TANPA tanda baca akhir (nama bab di daftar isi)
      • baris penanda daftar (Daftar Gambar/Tabel/Lampiran)
    Bukan daftar isi kalau: baris panjang (paragraf bahasan) atau berakhir
    dengan titik sebagai kalimat penuh (>120 kar).
    """
    if not baris:
        return False
    b = baris.strip()
    # penanda daftar seperti "Daftar Gambar"
    if _PENANDA_DAFTAR.match(b):
        return True
    # nomor / romawi / huruf pendek — khas daftar isi
    if re.fullmatch(r'(?:\d{1,3}|[IVXLCivxlc]{1,6}|[A-Za-z])\.?', b):
        return True
    # sangat pendek → hampir pasti baris daftar (nama bab)
    if len(b) <= 60:
        return True
    return False


def awal_isi_naskah(teks: str) -> int:
    """Posisi karakter AWAL ISI NASKAH — akhir dari bagian pembuka.

    🎯 INI AKAR MASALAHNYA (diukur 16Sep26 pada 6 dokumen nyata).

    KENAPA FUNGSI INI ADA
    =====================
    Semua tambalan sebelumnya berusaha MENDETEKSI BARIS DAFTAR ISI:
    titik pengarah, nomor menempel, baris membungkus, nomor halaman di ujung…
    Itu DAFTAR HITAM yang tak ada habisnya — tiap gaya baru (ke-14, ke-15, …)
    lolos lagi. Bukti: 5 dari 11 bagian peta skripsi Olahraga tetap PALSU
    walau sudah ditambal 4 kali.

    CARA BERPIKIR YANG BENAR: jangan cari SAMPAH, cari ISI.
    Isi naskah punya SATU pembeda yang berlaku di SEMUA dokumen:

        DAFTAR ISI   → judul bab SELALU diikuti NOMOR HALAMAN
                       "BAB I PENDAHULUAN ....... 1"
                       "BAB I PENDAHULUAN1"
                       "BAB I" + "PENDAHULUAN...........1"

        ISI NASKAH   → judul bab BERSIH, tanpa nomor halaman
                       "BAB I" + "PENDAHULUAN"
                       "BAB I    PENDAHULUAN"

    Jadi: awal isi = "BAB I" PERTAMA yang judulnya BERSIH. Semua sebelum itu
    = bagian pembuka (cover, abstrak, daftar isi, daftar tabel/gambar).

    HASIL UKUR (6 dokumen nyata — semuanya tepat):
        disertasi S3 kesehatan    → 7.4%   sisa='PENDAHULUAN'
        skripsi S1 olahraga       → 31.2%  sisa='PENDAHULUAN'
        skripsi S1 UNMUL          → 16.9%  'PENDAHULUAN'   (bukan 'PENDAHULUAN1')
        tesis S2 manajemen        → 14.6%  sisa='PENDAHULUAN'
        tesis S2 pendidikan bhs   → 17.1%  sisa='PENDAHULUAN'
        tesis S2 sastra           → 20.4%  sisa='PENDAHULUAN'

    Kembalikan 0 bila tidak yakin (aman: teks tidak dipotong).
    """
    if not teks:
        return 0
    for m in re.finditer(r'^[ \t]*(?i:BAB)[ \t]+I\b(?![IVXLC])(.*)$', teks, re.M):
        sisa = (m.group(1) or '').strip()
        nxt = [x.strip() for x in teks[m.end():m.end() + 120].split('\n')
               if x.strip()][:1]
        nxtv = nxt[0] if nxt else ''
        kandidat = sisa if sisa else nxtv
        if len(kandidat) < 3:
            continue
        if '....' in kandidat or '…' in kandidat:
            continue                        # titik pengarah → masih daftar isi
        if re.search(r'\d\s*$', kandidat):
            continue                        # nomor halaman → masih daftar isi
        # 🔴 BUG NYATA ke-18 (24Sep26, skripsi UIR dari web — ACC Bos).
        #    Versi lama hanya memeriksa baris BERIKUTNYA kalau `sisa` KOSONG:
        #         if not sisa and (nomor halaman / titik pengarah di nxtv)
        #    Akibat nyata: naskah yang menulis judul MENEMPEL
        #         "BAB I :PENDAHULUAN"
        #         "1.1 Latar Belakang Masalah .......... 1"   ← daftar isi!
        #    lolos 100%: `sisa` ada isinya → baris berikutnya tak diperiksa →
        #    baris DAFTAR ISI diterima sebagai awal isi naskah.
        #    Terukur pada skripsi UIR (127 hal): awal_isi = 7.590 padahal isi
        #    asli mulai 14.019 → daftar isi ikut masuk peta → nomor "1.1" dari
        #    daftar isi diambil (kemunculan terpanjang) → 2 bagian RAKSASA
        #    (51.156 & 51.659 kar) = separuh naskah salah alamat.
        #    PERBAIKAN: baris berikutnya diperiksa SELALU (sisa ada atau tidak).
        if nxtv and ('....' in nxtv or '…' in nxtv or re.search(r'\d\s*$', nxtv)):
            # baris berikutnya bertitik-pengarah / bernomor halaman → daftar isi
            # KECUALI judul menempel ini benar-benar judul bab (mis. ":PENDAHULUAN")
            # dan baris berikutnya adalah sub-bab isi TANPA titik pengarah.
            if not (len(nxtv) > 60 and len(nxtv.split()) > 8):
                continue
        return m.start()
    return 0


def buang_daftar_isi(teks: str) -> str:
    """Buang bagian PEMBUKA (cover, abstrak, daftar isi/tabel/gambar) dari teks.

    🎯 CARA KERJA (dirombak 16Sep26 atas arahan Bos: "jangan menambal-menambal,
    cari akar masalahnya, karena menambal benar sekarang tapi kasus lain salah"):

        awal = awal_isi_naskah(teks)     ← satu aturan, bukan daftar pola
        kalau awal > 0  → ambil teks[awal:]  (buang seluruh bagian pembuka)
        kalau awal = 0  → pakai pembersih konservatif di bawah (jaring pengaman)

    Daftar garis pembuang-per-baris di bawah DIPERTAHANKAN hanya sebagai jaring
    pengaman untuk teks tanpa "BAB I" (mis. artikel jurnal, proposal, dokumen
    umum) — di situ tidak ada penanda bab untuk dipakai.

    Aman: kalau hasil terlalu pendek (<30% asli), kembalikan teks asli.
    """
    if not teks:
        return ''

    # ── ATURAN AKAR: potong di awal isi naskah ────────────────────────────
    awal = awal_isi_naskah(teks)
    if awal > 0:
        hasil = teks[awal:]
        # pengaman: jangan sampai isi naskah hilang
        if len(hasil) >= len(teks) * 0.3:
            log.debug('[state] awal isi naskah di %d (%d→%d kar)',
                      awal, len(teks), len(hasil))
            return hasil
        log.warning('[state] awal isi di %d tapi sisa cuma %d kar '
                    '— pakai pembersih konservatif', awal, len(hasil))

    # 1) buang baris yang jelas baris daftar
    #    (a) pakai titik-titik pengarah → "1.1 Latar Belakang .... 3"
    #    (b) nomor halaman menempel → "BAB I PENDAHULUAN1" / "1.1Latar Belakang1"
    def _baris_daftar(b: str) -> bool:
        return bool(_POLA_BARIS_DAFTAR.search(b)
                    or _POLA_BARIS_DAFTAR_NEMPEL.match(b.strip())
                    or _POLA_BARIS_DAFTAR_TABEL.match(b.strip())
                    or _POLA_BARIS_DAFTAR_GAMBAR_NEMPEL.match(b.strip()))

    baris = [b for b in teks.split('\n') if not _baris_daftar(b)]

    # 1a-2) 🔴 BUG ke-14 (16Sep26, skripsi Olahraga UNHAS): daftar isi dengan
    #       nama sub-bab PANJANG membungkus jadi 2 baris, nomor halaman menempel
    #       di ujung baris KEDUA:
    #           "4.1 Data Distribusi Usia, Usia Pertama Haid, ..."
    #           "Atlet Kriket Pra PON 2021 yang Melakukan Latihan ... Selatan37"
    #       Baris kedua tidak cocok pola daftar apa pun → LOLOS → jadi sub-bab
    #       palsu 295 kar (peta = PENENTU HARGA → user ditagih salah).
    #       ATURAN AMAN (jangan boros): baris yang diakhiri angka HANYA dibuang
    #       bila baris SEBELUMNYA adalah baris daftar bernomor sub-bab. Ini
    #       mencegah paragraf bahasan asli yang kebetulan berakhir angka
    #       (mis. "…sebanyak 37") ikut terbuang.
    _no_subbab = re.compile(r'^\s*\d+\.\d+\.?\s')
    keluar2: list[str] = []
    for b in baris:
        if (keluar2 and _POLA_BARIS_DAFTAR_HAL.search(b)
                and _no_subbab.match(keluar2[-1].strip())):
            continue                     # lanjutan baris daftar isi → buang
        keluar2.append(b)
    baris = keluar2

    # 1b) blok DAFTAR ISI gaya "menempel": bila >2 baris berturut-turut cocok,
    #     itu blok daftar isi sungguhan → buang sampai baris non-daftar.
    keluar: list[str] = []
    run = 0
    for b in baris:
        if _baris_daftar(b):
            run += 1
            continue
        if run >= 2:
            keluar = keluar[:-run] if run <= len(keluar) else []
        keluar.append(b)
        run = 0
    baris = keluar
    bersih = '\n'.join(baris)

    # 2) buang blok daftar-daftar (DAFTAR ISI/TABEL/GAMBAR/LAMPIRAN/…)
    #    🔴 BUG NYATA (16Sep26, skripsi S1 nyata): versi lama begitu ketemu
    #    penanda daftar → "dilewati=True" dan HANYA berhenti kalau ketemu
    #    baris berisi PERSIS "BAB I". Pada naskah nyata, setelah
    #    "DAFTAR LAMPIRAN" isi naskah langsung mengalir (tanpa baris "BAB I"
    #    tersendiri), sehingga 808 baris isi — SELURUH BAB I–V — ikut terbuang.
    #    Perbaikan: blok daftar HANYA dibuang di WILAYAH AWAL dokumen
    #    (bagian pembuka), dan lewati BERHENTI juga saat ketemu penanda isi
    #    nyata: judul BAB, sub-bab bernomor, atau teks paragraf panjang.
    potong: list[str] = []
    dilewati = False
    # 🔴 BUG ke-10 (16Sep26, disertasi S3 323 hal): batas 15% terlalu kaku untuk
    # dokumen BESAR. 402.252 kar -> batas 60.337, padahal blok daftar berakhir
    # di ~6.200 kar. Batas baru: 15% ATAU minimal 30.000 kar.
    batas_awal = max(30_000, int(len(bersih) * 0.15))
    pos = 0
    # 🔴 BUG ke-4 (16Sep26): penanda daftar SERING muncul BERURUTAN tanpa isi
    # di antaranya — naskah nyata UNMUL:
    #     "DAFTAR ISI\nDAFTAR TABEL\nDAFTAR GAMBAR\nDAFTAR LAMPIRAN\n"
    # lalu isi naskah langsung mengalir. Dengan mode lewati biasa, blok ini
    # memakan JUDUL "BAB I" dan paragraf awalnya (BAB I sempat HILANG dari peta).
    # Aturan baru: kalau penanda daftar muncul lagi saat sedang melewati,
    # itu penanda BERURUTAN → tidak memperpanjang lewati.
    penanda_terakhir = -10**9
    for b in bersih.split('\n'):
        b_str = b.strip()
        pos += len(b) + 1
        if _PENANDA_DAFTAR.match(b_str):
            # DAFTAR PUSTAKA itu bagian SAH (bukan daftar isi) — jangan buang isinya
            if re.match(r'^\s*DAFTAR\s+PUSTAKA\s*$', b_str, re.IGNORECASE):
                dilewati = False
                potong.append(b)
                continue
            # Penanda berurutan (bug ke-4). Pada naskah UNMUL rantai
            # "DAFTAR ISI\nDAFTAR TABEL\nDAFTAR GAMBAR\nDAFTAR LAMPIRAN"
            # dulu mematikan lewati dan itu BENAR, karena setelahnya isi
            # naskah langsung mengalir tanpa blok daftar.
            # 🔴 BUG ke-10 (16Sep26, disertasi S3): pada disertasi, rantai
            # "Daftar Gambar\nDaftar Tabel\nDaftar Lampiran" diikuti
            # "BAB I\nPENDAHULUAN" yang MASIH bagian daftar isi. Mematikan
            # lewati di sini membuat baris itu jadi bab palsu 514 kar.
            # Perbaikan: TETAP melewati selama masih wilayah awal dokumen.
            # Aman karena lewati tetap akan berhenti begitu ketemu ISI NYATA
            # (judul BAB berjudul / sub-bab bernomor / paragraf panjang).
            berurutan = dilewati and (pos - penanda_terakhir) < 400
            penanda_terakhir = pos
            if berurutan and pos > batas_awal:
                dilewati = False        # blok daftar kosong di TENGAH naskah
            else:
                dilewati = pos <= batas_awal
            potong.append(b)
            continue
        if dilewati:
            # berhenti melewati begitu ketemu penanda ISI NYATA
            # 🔴 BUG ke-3 (16Sep26): blok DAFTAR TABEL juga harus berhenti di
            # JUDUL BAB sungguhan. Pada skripsi Kedokteran UNHAS, setelah
            # "DAFTAR TABEL" isi naskah mulai dengan "BAB I PENDAHULUAN" yang
            # BERSPASI (judul asli), sedangkan baris daftar isi memakai gaya
            # menempel ("BAB I PENDAHULUAN1"). Jadi: baris "BAB ...  <judul>"
            # yang BUKAN baris daftar = awal isi naskah.
            # 🔴 BUG ke-6 (16Sep26): judul BAB gaya MENEMPEL ("BAB IPENDAHULUAN")
            # juga harus dianggap awal isi naskah. Versi sebelumnya hanya
            # mengenali "BAB I <judul>" BERSPASI, sehingga pada naskah sintetis
            # uji, baris "BAB IPENDAHULUAN" + isinya ikut termakan blok daftar.
            # 🔴 BUG ke-10 (16Sep26, disertasi S3): baris "BAB I" yang berdiri
            # sendiri TEPAT setelah rantai penanda daftar
            #     "Daftar Tabel\nDaftar Lampiran\nBAB I\nPENDAHULUAN\nA. Latar Belakang"
            # masih bagian DAFTAR ISI (judul bab di daftar isi memang ditulis
            # persis "BAB I" lalu judulnya di baris berikutnya).
            # ⚠️ PENDEKATAN YANG GAGAL (jangan diulang): memakai "jarak dari
            # penanda daftar" (`dekat_penanda`) → salah sasaran, memakan
            # BAB I pada tesis S2 Sastra & Manajemen.
            # PENDEKATAN YANG BENAR: periksa ISI BARISNYA. Blok daftar isi
            # punya pola khas "BAB I" diikuti baris JUDUL lalu baris berNOMOR
            # ("1.1 Latar Belakang1"). Isi naskah asli membuka dengan paragraf
            # bahasan panjang. Jadi cukup lihat apakah SETELAH baris ini
            # langsung ada paragraf bahasan (>=180 kar) — kalau ya, ini awal isi.
            isi_nyata = bool(
                _POLA_JUDUL_BAB.match(b_str)
                or re.match(r'^\s*BAB\s+[IVXLC]{1,5}\s*\S', b_str, re.IGNORECASE)
                or re.match(r'^\s*\d+\.\d+\s+\S', b_str, re.IGNORECASE)
                or len(b_str) > 200          # paragraf bahasan sungguhan
            )
            # 🔴 BUG ke-11 (16Sep26): baris "BAB I" dari daftar isi sempat jadi
            # bab palsu. Sudah ditangani AKAR oleh `awal_isi_naskah()` di atas
            # (seluruh bagian pembuka dipotong sebelum sampai ke sini). Cek
            # baris-berikutnya DIPERTAHANKAN sebagai jaring pengaman untuk teks
            # yang tidak punya pola "BAB I ... PENDAHULUAN" (mis. dokumen umum).
            if isi_nyata and _POLA_JUDUL_BAB.match(b_str) and not b_str.strip()[4:].strip():
                dilanjut = _baris_setelahnya(bersih, pos)
                if dilanjut is not None and _masih_isi_daftar(dilanjut):
                    isi_nyata = False
            if isi_nyata:
                dilewati = False
        if not dilewati:
            potong.append(b)

    hasil = '\n'.join(potong)
    if len(hasil) < len(teks) * 0.3:
        # keamanan: kalau terlalu banyak terbuang, kembalikan yang versi
        # hanya-buang-baris-daftar (jangan sampai isi naskah hilang)
        log.warning('[state] buang_daftar_isi terlalu agresif '
                    '(%d -> %d) — pakai versi konservatif', len(teks), len(hasil))
        return bersih
    return hasil


def deteksi_subbab(teks: str, maks: int = 40) -> list[dict[str, Any]]:
    """Petakan sub-bab (1.1, 4.2, …) beserta jumlah karakternya.

    Dipakai untuk: (a) ingatan per sub-bab (tabel section_state), dan
    (b) DETEKSI BAB = PENENTU HARGA kuota (MASTER_PLAN §4.13).

    Aman terhadap teks kosong/None. DAFTAR ISI dibuang lebih dulu.
    """
    if not teks:
        return []
    teks = buang_daftar_isi(teks)

    # kumpulkan posisi setiap sub-bab, lalu potong isi antar posisi
    # _POLA_SUBBAB: grup(1)=bab, grup(2)=anak, grup(3)=judul
    kandidat: list[tuple[int, str, str]] = []
    for m in _POLA_SUBBAB.finditer(teks):
        nomor = f'{m.group(1)}.{m.group(2)}'
        judul = (m.group(3) or '').strip()
        baris_penuh = m.group(0)
        if _subbab_palsu(nomor, judul, baris_penuh):
            continue                      # kalimat statistik / daftar tabel
        kandidat.append((m.start(), nomor, judul))
    if not kandidat:
        #  ⭐ 05Okt26 (putusan Bos "A"): naskah bergaya HURUF ("A. Latar
        #     Belakang"). Terukur: 43 judul nyata, 0 sampah (2 naskah).
        #     Dipakai HANYA kalau x.y tidak ada → perilaku lama TIDAK berubah.
        #  ⚠️ Nomor diberi awalan 'A.' supaya unik & bisa dibedakan di UI.
        for m in _POLA_SUBBAB_HURUF.finditer(teks):
            nomor = m.group(1).upper()
            judul = (m.group(2) or '').strip()
            if not judul or _subbab_palsu(nomor, judul, m.group(0)):
                continue
            kandidat.append((m.start(), nomor, judul))
    if not kandidat:
        return []

    # Bila satu nomor muncul BERKALI (mis. "1.1" di ringkasan Bab I lalu di
    # Bab I asli), ambil kemunculan dengan isi TERPANJANG — itu isi sebenarnya.
    terbaik: dict[str, tuple[int, int, str]] = {}
    for idx, (pos, nomor, judul) in enumerate(kandidat):
        akhir = kandidat[idx + 1][0] if idx + 1 < len(kandidat) else len(teks)
        panjang = akhir - pos
        lama = terbaik.get(nomor)
        if not lama or panjang > lama[1]:
            terbaik[nomor] = (pos, panjang, judul)

    # urutkan lagi sesuai posisi di dokumen
    dipilih = sorted(terbaik.items(), key=lambda kv: kv[1][0])

    hasil: list[dict[str, Any]] = []
    for nomor, (pos, panjang, judul) in dipilih[:maks]:
        isi = teks[pos:pos + panjang]
        judul_baku = title_for(nomor)
        hasil.append({
            'section_id': nomor,
            # 🚨 BUG ke-16 (16Sep26, skripsi S1 Olahraga UNHAS) — BUG BAHAYA.
            #    Urutan lama `judul_baku or judul` membuat JUDUL BAKU KODE
            #    MENANG atas JUDUL ASLI NASKAH. Akibat nyata:
            #        naskah asli : "2.1.3 Fisiologi siklus menstruasi"
            #        peta ke AI  : "2.1 Landasan Teori"     ← SALAH KONTEKS
            #    AI lalu disuruh merevisi "Landasan Teori" padahal isinya tentang
            #    siklus menstruasi → AI menulis teori umum yang TIDAK NYAMBUNG
            #    dengan isi naskah. Ini kemungkinan besar akar keluhan
            #    "kata tidak nyambung" (MASTER_PLAN §4.13).
            #    ATURAN BARU: JUDUL ASLI NASKAH SELALU MENANG. Judul baku kode
            #    hanya dipakai bila naskah TIDAK punya judul sama sekali.
            'section_title': judul or judul_baku or f'Sub-bab {nomor}',
            'kategori': get_category_for(nomor),
            'char_count': len(isi),
            'isi_teks': isi,
        })
    log.debug('[state] terdeteksi %d sub-bab dari %d karakter', len(hasil), len(teks))
    return hasil


def deteksi_bab_besar(teks: str) -> list[dict[str, Any]]:
    """Deteksi BAB (I–V) beserta ukurannya — untuk deteksi kasar & harga.

    KENAPA terpisah dari deteksi_subbab: tidak semua naskah punya sub-bab
    bernomor (proposal, dokumen umum). Bab besar = jaring pengaman.
    """
    if not teks:
        return []
    # 🚨 BUG ke-13 (16Sep26): `deteksi_subbab` memanggil `buang_daftar_isi`
    #    sendiri, tapi `deteksi_bab_besar` TIDAK — padahal `petakan()` bisa
    #    memakai fungsi ini langsung. Akibatnya DAFTAR ISI MENTAH ikut dibaca
    #    sebagai bab. Bukti pada tesis S2 Manajemen: "BAB VI PEMBAHASAN .... 79"
    #    terbaca sebagai bab 244 kar (padahal itu baris daftar isi dengan
    #    titik-pengarah + nomor halaman).
    #    Aman: `buang_daftar_isi` mengembalikan teks apa adanya kalau tidak ada
    #    penanda, dan punya pengaman sendiri kalau terlalu agresif.
    teks = buang_daftar_isi(teks)
    # _POLA_BAB: grup(1) = nomor romawi ('I'), grup(2) = judul (boleh kosong/menempel)
    kandidat: list[tuple[int, str, str]] = []
    #  ⭐ 05Okt26 (temuan gerbang `_uji_presisi_dropdown_http`): naskah template
    #     UNMUL memuat KALIMAT PENGARAH "Bab 4 dan Bab 5 dapat Anda tulis
    #     setelah…" → ikut tertangkap pola angka Arab → bab PALSU (BAB 4).
    #     BUKTI: naskah yang sama menulis bab aslinya sebagai ROMAWI (BAB IV).
    #     ATURAN (bukan tambalan): kalau di naskah ini sudah ADA bab bermomor
    #     ROMAWI, maka bentuk ANGKA ARAB hanya sah bila judulnya KHAS
    #     (tidak muncul sebagai kalimat pengarah). Cara paling aman & sederhana:
    #     angka Arab HANYA dihitung kalau judulnya HURUF BESAR semua (ciri judul
    #     bab), BUKAN kalimat ("dan Bab 5 dapat Anda tulis…").
    _ada_romawi = any(m.group(1).isalpha()
                      for m in _POLA_BAB.finditer(teks))
    for m in _POLA_BAB.finditer(teks):
        nomor_m = m.group(1).upper()
        judul = (m.group(2) or '').strip()
        if nomor_m.isdigit():
            # kalimat pengarah selalu punya huruf kecil setelah nomor
            if judul and judul[0].islower():
                continue
            # di naskah yang memakai romawi, angka Arab = kutipan/penunjuk
            if _ada_romawi:
                continue
        if not judul or _POLA_BARIS_SAMPAH.match(judul):
            # BUG ke-9: judul sering di baris BERIKUTNYA ("BAB I\nPENDAHULUAN")
            judul = _judul_dari_baris_berikut(teks, m.end())
        else:
            judul = re.sub(r'\s+\d{1,3}\s*$', '', judul).strip()
        kandidat.append((m.start(), f'BAB {nomor_m}', judul))
    #  ⭐ 05Okt26 (putusan Bos "A"): bentuk "IV. HASIL DAN PEMBAHASAN"
    #     (romawi + TITIK, TANPA kata "BAB") — nyata di 290462754.pdf.
    #     Terukur aman: 18 naskah asli → 2 bab tertangkap, 0 sampah.
    #     ⚠️ Nomor dinormalkan jadi 'BAB IV' supaya aturan "nomor kembar →
    #     ambil terpanjang" & get_category_for() tetap bekerja.
    _sudah = {m.group(1).upper() for m in _POLA_BAB.finditer(teks)}
    for m in _POLA_BAB_TITIK.finditer(teks):
        nomor_rom = m.group(1).upper()
        if nomor_rom in _sudah:              # sudah tertangkap _POLA_BAB
            continue
        kandidat.append((m.start(), f'BAB {nomor_rom}', m.group(2).strip()))
    if not kandidat:
        return []

    # 🚨 BUG ke-12 (16Sep26, disertasi S3 + skripsi olahraga): `deteksi_bab_besar`
    #    TIDAK memakai aturan "nomor kembar → ambil TERPANJANG" yang sudah lama
    #    dipakai `deteksi_subbab`. Akibatnya SEMUA kemunculan "BAB X" masuk peta,
    #    termasuk yang berasal dari DAFTAR ISI (514 kar) atau kutipan
    #    ("sebagaimana dijelaskan pada BAB II"). Peta jadi punya bab PALSU.
    #    Bahaya nyata: peta = PENENTU HARGA kuota → bab palsu = user ditagih salah,
    #    dan Buku Catatan AI menandai bagian yang salah.
    #    Aturan: satu nomor hanya boleh muncul SEKALI — pilih isi TERPANJANG.
    terbaik: dict[str, tuple[int, int, str]] = {}
    for idx, (pos, nomor, judul) in enumerate(kandidat):
        akhir = kandidat[idx + 1][0] if idx + 1 < len(kandidat) else len(teks)
        panjang = akhir - pos
        lama = terbaik.get(nomor)
        if not lama or panjang > lama[1]:
            terbaik[nomor] = (pos, panjang, judul)
    dipilih = sorted(terbaik.items(), key=lambda kv: kv[1][0])

    hasil: list[dict[str, Any]] = []
    for nomor, (pos, panjang, _j) in dipilih:
        judul = _j
        isi = teks[pos:pos + panjang]
        hasil.append({
            'section_id': nomor,                    # 'BAB I'
            'section_title': judul or nomor,
            # ⭐ 05Okt26 AKAR DIPERBAIKI: dulu harfiah 'bab' → Mode Belajar
            #    tak pernah terbuka (belajar.py cari 'bab1'..'bab5').
            #    Penulis kategori kini SATU bentuk dengan deteksi_subbab.
            'kategori': get_category_for(nomor),
            'char_count': len(isi),
            'isi_teks': isi,
        })
    return hasil


def petakan(teks: str, catatan_satpam: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Petakan naskah: pakai sub-bab kalau ada, kalau tidak pakai BAB besar.

    Ini yang dipakai jalur biaya kuota: 1 unit = 1 sub-bab ATAU 1 bab.

    `catatan_satpam` (opsional, 05Okt26) — hasil app/satpam.periksa().

    ⭐ PUTUSAN BOS (05 Okt 2026) = "B":
        DUA-DUANYA SAH, dipakai sesuai keperluan —
           · peta BAB besar  → konteks AI & panel Belajar (kategori bab1..bab5)
           · peta sub-bab    → satuan harga kuota (kecil = murah)
        ⇒ Satpam TIDAK memilih di sini. Satpam hanya MEMERIKSA jumlahnya
          dan menandai keganjilan (confidence rendah → pintu TANYA).

    Fungsi ini TIDAK PERNAH menggagalkan pemetaan karena satpam — kalau
    satpam mati (galat/jaringan), jalur lama tetap jalan apa adanya.
    """
    sub = deteksi_subbab(teks)
    if len(sub) >= 3:                                # cukup banyak -> pakai sub-bab
        return sub
    bab = deteksi_bab_besar(teks)
    if bab:
        log.info('[state] hanya %d sub-bab terdeteksi -> pakai %d BAB besar',
                 len(sub), len(bab))
        return bab
    # fallback terakhir: seluruh dokumen jadi 1 unit
    return [{
        'section_id': '__seluruh__',
        'section_title': 'Seluruh Dokumen',
        'kategori': 'bab',
        'char_count': len(teks or ''),
        'isi_teks': teks or '',
    }]


def peta_bab_besar(teks: str) -> list[dict[str, Any]]:
    """Peta per BAB BESAR saja — untuk konteks AI & panel Belajar.

    ⭐ 05Okt26 (putusan Bos B): dipakai BERSAMAAN dengan peta sub-bab,
    bukan menggantikan. Panel Belajar butuh kategori 'bab1'..'bab5'.
    """
    return deteksi_bab_besar(teks) or []


def ringkas_peta(peta: list[dict[str, Any]]) -> str:
    """Ringkasan peta untuk log/tampilan."""
    if not peta:
        return '(peta kosong)'
    baris = [f'  {len(peta)} bagian:']
    for p in peta[:30]:
        baris.append(f"    {p['section_id']:10s} {p['section_title'][:32]:32s} "
                     f"{p['char_count']:>8,} kar  [{p['kategori']}]")
    if len(peta) > 30:
        baris.append(f'    … dan {len(peta) - 30} bagian lagi')
    return '\n'.join(baris)
