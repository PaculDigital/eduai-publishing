"""
app/jenis.py — LAPIS 1: DETEKSI JENIS DOKUMEN (EduAi)

MASTER_PLAN.md §4.16 (ACC Bos 15Sep26) — ATURAN KRUSIAL.
Arah Bos verbatim:
    "Layer1 AI harus paham jalur. Deteksi file dokumen. Apakah ini skripsi,
     apakah ini skripsi bab I, apakah ini skripsi bab I,II,III dst. Apakah ini
     tesis dst. Apakah ini file dokumen umum, perjanjian, nota, invoice dll. …
     AI harus bisa bedakan mana Skripsi mana Kelas Tesis.
     JANGAN SAMA BISA BAHAYA."

KENAPA INI KRUSIAL (bukan sekadar label):
    Salah jenjang → AI merevisi dengan STANDAR SALAH → naskah user RUSAK.
    Contoh nyata: disertasi S3 WAJIB punya temuan baru (novelty) + kontribusi
    teoretis. Kalau direvisi dengan standar skripsi S1, AI akan:
      • menuntut "cukup 2-3 hipotesis" padahal S3 sah punya 5-7
      • mengabaikan keharusan kontribusi teori
      • menyederhanakan yang seharusnya dalam
    Mahasiswa S3 lalu mempertahankan naskah hasil AI di sidang → DITOLAK.

FILOSOFI (mengikuti penelitian-bot, READ-ONLY sumber cetak biru):
    Deteksi BERLAPIS dan GRATIS (Rp 0) — aturan bobot dulu, tanpa AI.
    AI hanya dipanggil kalau ragu DAN pemanggil mengizinkan (hemat biaya).

PRINSIP TANYA KE USER (§4.17, aturan induk):
    • AI YAKIN (bukti kuat) → PUTUSKAN SENDIRI, tampilkan sebagai PERNYATAAN.
    • AI RAGU (tidak ada kata kunci jenjang) → TANYA USER 1x dengan pilihan.
      Ini SENGAJA menyimpang dari aturan umum "AI putuskan sendiri", karena
      salah jenjang = naskah rusak (Bos: "Tanya user, agar ai tidak tersesat
      di kemudian hari").
    • Selalu sediakan tombol koreksi — user harus bisa menimpa hasil deteksi.

SUMBER BUKTI (dipakai berlapis, dari yang paling kuat):
    1. COVER / halaman judul  — bobot TERBESAR (= kata kunci resmi naskah)
    2. Kata kunci jenjang di seluruh naskah ("TESIS", "MAGISTER", "DISERTASI")
    3. Struktur bab yang ada (BAB I–V lengkap vs hanya BAB I)
    4. Isi/format (perjanjian, nota, invoice, surat → dokumen_umum)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ═══════════════════════════════════════════════════════════════════════════
# 6 JENIS DOKUMEN (ACC Bos 15Sep26) — DAFTAR TERTUTUP, JANGAN DITAMBAH
# tanpa ACC baru. Kunci ini dipakai konsisten di seluruh sistem
# (brief.py, profil_dokumen.jenjang, prompt, dsb).
# ═══════════════════════════════════════════════════════════════════════════
JENIS_SKRIPSI = 'skripsi'                 # S1
JENIS_TESIS = 'tesis'                     # S2
JENIS_DISERTASI = 'disertasi'             # S3
JENIS_ARTIKEL = 'artikel_jurnal'          # naskah jurnal, penomoran polos
JENIS_PROPOSAL = 'proposal'               # usulan penelitian (belum BAB IV-V)
JENIS_UMUM = 'dokumen_umum'               # JALUR KHUSUS NON-AKADEMIK

JENIS_AKADEMIK = (JENIS_SKRIPSI, JENIS_TESIS, JENIS_DISERTASI,
                  JENIS_ARTIKEL, JENIS_PROPOSAL)

# ═══════════════════════════════════════════════════════════════════════════
# 🆕 JENIS BUKU (ACC Bos 19 Okt 2026) — DAFTAR TERBUKA, mengikuti 5 kartu
#    Publish Buku di `app/buku.py`. Kode di sini HARUS sama dengan 'kode' di
#    JENIS_BUKU supaya 1 buku punya SATU identitas di seluruh sistem.
#
# ⚠️ KENAPA DIPISAH DARI JENIS_AKADEMIK: buku BUKAN skripsi/tesis. Jev & Hakim
#    dilatih untuk peta naskah skripsi (BAB I–V). Memakai mereka di buku =
#    SALAH ALAT. Pemisahan ini yang membuat "salah alat" jadi MUSTAHIL,
#    bukan sekadar diingat-ingat.
# ═══════════════════════════════════════════════════════════════════════════
JENIS_BUKU_AJAR = 'buku_ajar'
JENIS_BUKU_UMUM = 'buku_umum'
JENIS_BUKU_MONOGRAF = 'buku_monograf'
JENIS_BOOK_CHAPTER = 'book_chapter'
JENIS_BUKU_REFERENSI = 'buku_referensi'

JENIS_BUKU = (JENIS_BUKU_AJAR, JENIS_BUKU_UMUM, JENIS_BUKU_MONOGRAF,
              JENIS_BOOK_CHAPTER, JENIS_BUKU_REFERENSI)

# 4 KATEGORI (brief.py baris 39) — dipakai untuk menentukan mode kerja AI.
KAT_1BAB = 'akademik_1bab'                # hanya 1 bab (mis. Bab I saja)
KAT_PROPOSAL = 'akademik_proposal'        # BAB I-III (usulan)
KAT_LENGKAP = 'akademik_lengkap'          # BAB I-V lengkap
KAT_UMUM = 'dokumen_umum'                 # non-akademik

# ── Label ramah-pengguna (langsung tampil di layar; DILARANG jargon) ──────
LABEL_JENIS: dict[str, str] = {
    JENIS_SKRIPSI:  'Skripsi (S1)',
    JENIS_TESIS:    'Tesis (S2)',
    JENIS_DISERTASI:'Disertasi (S3)',
    JENIS_ARTIKEL:  'Artikel Jurnal',
    JENIS_PROPOSAL: 'Proposal Penelitian',
    JENIS_UMUM:     'Dokumen Umum (bukan naskah akademik)',
    JENIS_BUKU_AJAR:      'Buku Ajar',
    JENIS_BUKU_UMUM:      'Buku Umum',
    JENIS_BUKU_MONOGRAF:  'Buku Monograf',
    JENIS_BOOK_CHAPTER:   'Book Chapter',
    JENIS_BUKU_REFERENSI: 'Buku Referensi',
}

# ═══════════════════════════════════════════════════════════════════════════
# BEDA STANDAR PER JENJANG — INTI dari modul ini.
#
# Sumber: penelitian-bot/agents/bidang-explorer.js baris 120-126 (tabel emas
# `jenjangInfo`) + ethics-checker.js + catatan koreksi Bos (tesis bisa sampai
# 12 hipotesis karena mediasi ganda pararel — JANGAN pakai angka S1).
# ═══════════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class Standar:
    """Aturan akademik yang BEDA per jenjang. Dipakai menyusun prompt revisi."""
    jenjang_resmi: str
    label: str
    durasi: str
    sumber_data: str
    metode: str
    hipotesis_min: int
    hipotesis_maks: int
    wajib_novelty: bool
    wajib_kontribusi_teori: bool
    kedalaman_pembahasan: str
    catatan: str


STANDAR: dict[str, Standar] = {
    JENIS_SKRIPSI: Standar(
        jenjang_resmi='S1 (Sarjana)',
        label='Skripsi',
        durasi='4-6 bulan',
        sumber_data='data sekunder / survei sederhana',
        metode='metode standar (regresi berganda, statistik deskriptif, kualitatif dasar)',
        hipotesis_min=2, hipotesis_maks=3,
        wajib_novelty=False,
        wajib_kontribusi_teori=False,
        kedalaman_pembahasan=('Membahas hasil apa adanya. CUKUP menjawab rumusan '
                              'masalah. Tidak dituntut kontribusi teoretis baru.'),
        catatan=('Definisi Operasional variabel diletakkan di BAB III (Metode), '
                 'BUKAN BAB I — penempatan di Bab I akan ditolak dosen '
                 '(konvensi S1 Indonesia).'),
    ),
    JENIS_TESIS: Standar(
        jenjang_resmi='S2 (Magister)',
        label='Tesis',
        durasi='6-12 bulan',
        sumber_data='data primer + sekunder',
        metode=('metode lanjutan (SEM/PLS, analisis mediasi, moderasi, '
                'analisis jalur, kualitatif mendalam)'),
        # 🔴 KOREKSI BOS 15Sep26: tesis BISA SAMPAI 12 hipotesis (dual mediasi
        # PARAREL). JANGAN warisi angka S1 (2-3) ke tesis — itu melemahkan naskah.
        hipotesis_min=2, hipotesis_maks=12,
        wajib_novelty=True,
        wajib_kontribusi_teori=True,
        kedalaman_pembahasan=('Membahas hasil dengan MODEL: mediasi/moderasi harus '
                              'dijelaskan mekanismenya, bukan hanya signifikansinya. '
                              'Wajib membandingkan hasil dengan penelitian terdahulu.'),
        catatan=('Model mediasi GANDA (paralel/serial) SAH dan lazim. Hipotesis '
                 'boleh banyak (s.d. 12) — JANGAN suruh mahasiswa memangkas '
                 'hipotesis yang sudah benar.'),
    ),
    JENIS_DISERTASI: Standar(
        jenjang_resmi='S3 (Doktor)',
        label='Disertasi',
        durasi='12-24 bulan',
        sumber_data='data orisinal lapangan',
        metode=('kontribusi kebaruan metodologi/teori; boleh mengembangkan '
                'instrumen, model, atau kerangka baru'),
        hipotesis_min=3, hipotesis_maks=12,
        wajib_novelty=True,                # WAJIB — ini syarat kelulusan S3
        wajib_kontribusi_teori=True,
        kedalaman_pembahasan=('Membahas dengan KEDALAMAN TEORETIS: harus ada '
                              'temuan baru (novelty), kontribusi teori, dan '
                              'implikasi teoretis — bukan sekadar praktis.'),
        catatan=('SYARAT KELULUSAN S3: temuan baru + kontribusi teoretis. '
                 'Kalau revisi menghapus/menumpulkan sisi teoretis, revisi itu '
                 'MERUSAK naskah. DILARANG menyederhanakan ke standar S1/S2.'),
    ),
    JENIS_ARTIKEL: Standar(
        jenjang_resmi='Artikel Jurnal',
        label='Artikel Jurnal',
        durasi='menyesuaikan terbitan',
        sumber_data='mengikuti naskah',
        metode='mengikuti naskah',
        hipotesis_min=0, hipotesis_maks=12,
        wajib_novelty=True,
        wajib_kontribusi_teori=True,
        kedalaman_pembahasan=('Ringkas, padat, mengikuti gaya jurnal. '
                              'Pembahasan fokus pada kebaruan & implikasi.'),
        catatan=('Penomoran POLOS tanpa "BAB" (Pendahuluan → Metode → Hasil → '
                 'Diskusi → Simpulan). DILARANG memaksakan struktur 5 bab. '
                 'Ada abstrak, kata kunci, daftar pustaka gaya jurnal.'),
    ),
    JENIS_PROPOSAL: Standar(
        jenjang_resmi='Proposal Penelitian',
        label='Proposal',
        durasi='tahap usulan',
        sumber_data='rencana pengumpulan data',
        metode='direncanakan (belum dijalankan)',
        hipotesis_min=0, hipotesis_maks=12,
        wajib_novelty=True,
        wajib_kontribusi_teori=False,
        kedalaman_pembahasan=('Hanya BAB I-III. BELUM ada HASIL. DILARANG '
                              'mengarang temuan, angka, atau pembahasan hasil.'),
        catatan=('Penanda proposal: naskah berhenti di BAB III (Metode), tidak '
                 'ada BAB IV/V berisi hasil. Kalau user minta "pembahasan hasil" '
                 'padahal ini proposal → tolak dengan sopan, jelaskan datanya '
                 'belum ada.'),
    ),
    JENIS_UMUM: Standar(
        jenjang_resmi='Non-akademik',
        label='Dokumen Umum',
        durasi='—',
        sumber_data='—',
        metode='—',
        hipotesis_min=0, hipotesis_maks=0,
        wajib_novelty=False,
        wajib_kontribusi_teori=False,
        kedalaman_pembahasan=('BUKAN naskah akademik. DILARANG memaksakan '
                              'struktur BAB, hipotesis, sitasi APA, atau '
                              '"tinjauan pustaka".'),
        catatan=('Contoh: perjanjian, nota dinas, invoice, surat, laporan, '
                 'prosedur/SOP. Yang dibenahi: kejelasan, tata bahasa, '
                 'kelengkapan unsur dokumen, konsistensi pihak/tanggal/nominal.'),
    ),
    # ── BUKU (ACC Bos 19 Okt 2026) ────────────────────────────────────────
    #  Buku BUKAN naskah akademik berjenjang: tidak ada pembimbing, tidak ada
    #  sidang, tidak ada hipotesis. Karena itu standarnya juga BUKAN S1/S2/S3.
    JENIS_BUKU_AJAR: Standar(
        jenjang_resmi='Buku Ajar',
        label='Buku Ajar',
        durasi='menyesuaikan RPS',
        sumber_data='RPS / bahan ajar penulis',
        metode='mengikuti capaian pembelajaran (OBE)',
        hipotesis_min=0, hipotesis_maks=0,
        wajib_novelty=False, wajib_kontribusi_teori=False,
        kedalaman_pembahasan=('Berbasis capaian pembelajaran: tiap bab punya '
                              'tujuan, uraian, latihan, dan ringkasan. '
                              'DILARANG memaksakan hipotesis atau novelty.'),
        catatan=('Struktur mengikuti RPS, BUKAN BAB I-V skripsi.'),
    ),
    JENIS_BUKU_UMUM: Standar(
        jenjang_resmi='Buku Umum',
        label='Buku Umum',
        durasi='—',
        sumber_data='tema / pengalaman penulis',
        metode='naratif',
        hipotesis_min=0, hipotesis_maks=0,
        wajib_novelty=False, wajib_kontribusi_teori=False,
        kedalaman_pembahasan=('Naratif dan mengalir. DILARANG memaksakan '
                              'struktur BAB akademik, hipotesis, atau sitasi APA '
                              'kaku. Sapaan mengikuti jenis pembaca.'),
        catatan='Struktur bab bebas; boleh ada ilustrasi dan glosarium.',
    ),
    JENIS_BUKU_MONOGRAF: Standar(
        jenjang_resmi='Monograf',
        label='Buku Monograf',
        durasi='—',
        sumber_data='hasil penelitian penulis (skripsi/tesis/disertasi)',
        metode='mengikuti penelitian asal',
        hipotesis_min=0, hipotesis_maks=0,
        wajib_novelty=True, wajib_kontribusi_teori=False,
        kedalaman_pembahasan=('Satu topik, satu temuan. DILARANG memaksakan '
                              'hipotesis baru di luar penelitian asal.'),
        catatan='Berasal dari SATU penelitian; struktur mengikuti temuan.',
    ),
    JENIS_BOOK_CHAPTER: Standar(
        jenjang_resmi='Book Chapter',
        label='Book Chapter',
        durasi='—',
        sumber_data='tema yang ditetapkan editor buku',
        metode='mengikuti tema editor/penerbit',
        hipotesis_min=0, hipotesis_maks=0,
        wajib_novelty=False, wajib_kontribusi_teori=False,
        kedalaman_pembahasan=('Satu bab dalam buku bersama; bahasan harus '
                              'fokus pada tema yang ditetapkan editor.'),
        catatan='Penulis banyak; panjang biasanya dibatasi penerbit.',
    ),
    JENIS_BUKU_REFERENSI: Standar(
        jenjang_resmi='Buku Referensi',
        label='Buku Referensi',
        durasi='—',
        sumber_data='literatur/kepustakaan',
        metode='telaah pustaka',
        hipotesis_min=0, hipotesis_maks=0,
        wajib_novelty=False, wajib_kontribusi_teori=True,
        kedalaman_pembahasan=('Rujukan ilmiah: setiap pernyataan bersandar '
                              'pada sumber. Ada daftar pustaka dan indeks.'),
        catatan='Wajib daftar pustaka + indeks subjek/nama.',
    ),
}

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 PORSI ALAT — SATU SUMBER KEBENARAN (ACC Bos 19 Okt 2026)
#
#    Bos verbatim: "harus punya id sendiri ... agar menggunakan jev dan hakim
#    tepat dan tidak salah alat, tau ini dokumen perlu jev, hakim atau tidak,
#    kalo perlu sudah sesuai porsinya."
#
#    ATURAN: alat dipilih dari ID DOKUMEN, BUKAN ditebak dari isi naskah.
#    ⇒ Buku MUSTAHIL dikirim ke Jev/Hakim; skripsi MUSTAHIL kehilangan peta.
# ═══════════════════════════════════════════════════════════════════════════
PORSI_ALAT: dict[str, dict] = {
    # Jev = SURVEYOR peta bab (dilatih untuk strukturnya naskah skripsi).
    # Hakim = pemfokus setelah peta, sebelum mesin & AI. Keduanya SENYAWA:
    # Jev tanpa Hakim = peta mentah dipakai mentah.
    JENIS_SKRIPSI:   {'jev': True,  'hakim': True,  'mutu_buku': False},
    JENIS_TESIS:     {'jev': True,  'hakim': True,  'mutu_buku': False},
    JENIS_DISERTASI: {'jev': True,  'hakim': True,  'mutu_buku': False},
    JENIS_ARTIKEL:   {'jev': True,  'hakim': True,  'mutu_buku': False},
    JENIS_PROPOSAL:  {'jev': True,  'hakim': True,  'mutu_buku': False},

    # Buku: Jev/Hakim DIMATIKAN — bentuknya lain (bab–sub-bab–sub-sub-bab,
    # glosarium, indeks, ilustrasi). Yang mengawasi = pemeriksa mutu buku.
    JENIS_BUKU_AJAR:      {'jev': False, 'hakim': False, 'mutu_buku': True},
    JENIS_BUKU_UMUM:      {'jev': False, 'hakim': False, 'mutu_buku': True},
    JENIS_BUKU_MONOGRAF:  {'jev': False, 'hakim': False, 'mutu_buku': True},
    JENIS_BOOK_CHAPTER:   {'jev': False, 'hakim': False, 'mutu_buku': True},
    JENIS_BUKU_REFERENSI: {'jev': False, 'hakim': False, 'mutu_buku': True},

    # Dokumen umum (surat/nota/invoice): tidak ada peta bab, tidak ada mutu buku.
    JENIS_UMUM:      {'jev': False, 'hakim': False, 'mutu_buku': False},
}

# Saat ID tidak dikenal: JANGAN menebak. Semua alat MATI (paling aman).
PORSI_ALAT_TAK_DIKENAL = {'jev': False, 'hakim': False, 'mutu_buku': False}


def porsi_alat(jenis: str | None) -> dict:
    """Alat apa yang boleh bekerja untuk jenis dokumen ini. Rp 0, tanpa AI.

    Bentuk balasan SELALU punya 3 kunci (jev/hakim/mutu_buku) supaya pemanggil
    tidak perlu cek `None`. ID tak dikenal → semua False (fail-safe).

    >>> porsi_alat('buku_umum')['jev']
    False
    >>> porsi_alat('skripsi')['jev']
    True
    """
    kunci = (jenis or '').strip()
    return dict(PORSI_ALAT.get(kunci, PORSI_ALAT_TAK_DIKENAL))


def perlu_jev(jenis: str | None) -> bool:
    return porsi_alat(jenis)['jev']


def perlu_hakim(jenis: str | None) -> bool:
    return porsi_alat(jenis)['hakim']


def perlu_mutu_buku(jenis: str | None) -> bool:
    return porsi_alat(jenis)['mutu_buku']


def apakah_buku(jenis: str | None) -> bool:
    """True kalau ini salah satu dari 5 jenis buku."""
    return (jenis or '').strip() in JENIS_BUKU

# ═══════════════════════════════════════════════════════════════════════════
# KAMUS KATA KUNCI — BERBOBOT, dan dipisah: KUAT vs LEMAH.
#
# PELAJARAN: kata umum ("skripsi" muncul sekali di kalimat "seperti skripsi pada
# umumnya") TIDAK boleh mengalah atas "MAGISTER"/"DISERTASI". Karena itu bobot
# kata KUAT jauh lebih besar dan dipakai di wilayah COVER (bobot x3).
# ═══════════════════════════════════════════════════════════════════════════
KATA_KUAT: dict[str, list[tuple[str, int]]] = {
    JENIS_SKRIPSI: [
        (r'\bskripsi\b', 10),
        (r'\bsarjana\s*\(?\s*s-?1\s*\)?', 8),
        (r'\bprogram\s+studi\s+s-?1\b', 8),
        (r'\bstrata\s*(?:satu|1|i)\b', 8),
        (r'\bujian\s+(?:skripsi|sarjana|pendadaran)\b', 6),
    ],
    JENIS_TESIS: [
        (r'\btesis\b', 10),
        (r'\bmagister\b', 10),
        (r'\bs-?2\b', 8),
        (r'\bstrata\s*(?:dua|2|ii)\b', 8),
        (r'\bprogram\s+magister\b', 10),
        (r'\bujian\s+tesis\b', 6),
        (r'\bsekolah\s+pascasarjana\b', 8),
    ],
    JENIS_DISERTASI: [
        (r'\bdisertasi\b', 12),
        (r'\bdoktor(?:al)?\b', 10),
        (r'\bs-?3\b', 8),
        (r'\bstrata\s*(?:tiga|3|iii)\b', 8),
        (r'\bprogram\s+doktor\b', 12),
        (r'\bpromosi\s+doktor\b', 8),
    ],
    JENIS_ARTIKEL: [
        (r'\b(naskah|artikel|manuskrip)\s+(?:jurnal|ilmiah)\b', 8),
        (r'\bjournal\s+(?:article|manuscript)\b', 8),
        (r'\bsubmit(?:ted)?\s+to\b', 5),
        (r'\b(?:jurnal|journal)\s+[a-z][a-z\s]+(?:vol\.?|volume)\b', 6),
        (r'\bkata\s+kunci\s*:', 5),
        (r'\bkeywords?\s*:', 5),
    ],
    JENIS_PROPOSAL: [
        (r'\bproposal\s+(?:penelitian|skripsi|tesis|disertasi)\b', 10),
        (r'\busulan\s+penelitian\b', 10),
        (r'\bresearch\s+proposal\b', 8),
    ],
    JENIS_UMUM: [
        (r'\bsurat\s+perjanjian\b', 12),
        (r'\bperjanjian\s+kerja\s*sama\b', 12),
        (r'\bmemorandum\s+of\s+understanding\b', 12),
        (r'\bnota\s+kesepahaman\b', 10),
        (r'\bnota\s+dinas\b', 10),
        (r'\binvoice\b', 12),
        (r'\bkwitansi\b', 12),
        (r'\bfaktur\b', 10),
        (r'\bsurat\s+pesanan\b', 10),
        (r'\bsurat\s+kuasa\b', 10),
        (r'\bsurat\s+keterangan\b', 8),
        (r'\bstandar\s+operasional\s+prosedur\b', 10),
        (r'\bpoin?\s+\d+\s*[\.\)]', 2),   # struktur berpasal
    ],
}

# Kata LEMAH: muncul di naskah akademik mana pun, bukan penanda jenjang.
KATA_LEMAH: list[tuple[str, int]] = [
    (r'\blatar\s+belakang\b', 2), (r'\brumusan\s+masalah\b', 2),
    (r'\btinjauan\s+pustaka\b', 2), (r'\bmetod(?:e|ologi)\s+penelitian\b', 2),
    (r'\bhipotesis\b', 2), (r'\bdosen\s+pembimbing\b', 3),
    (r'\bdaftar\s+pustaka\b', 2), (r'\babstrak\b', 2),
    (r'\bbab\s+[ivx]+\b', 1),
]

# Penanda JENIS STRUKTUR (untuk kategori: 1bab / proposal / lengkap)
_POLA_BAB = {
    'I':   re.compile(r'^\s*(?:BAB\s+I)\b', re.MULTILINE | re.IGNORECASE),
    'II':  re.compile(r'^\s*(?:BAB\s+II)\b', re.MULTILINE | re.IGNORECASE),
    'III': re.compile(r'^\s*(?:BAB\s+III)\b', re.MULTILINE | re.IGNORECASE),
    'IV':  re.compile(r'^\s*(?:BAB\s+IV)\b', re.MULTILINE | re.IGNORECASE),
    'V':   re.compile(r'^\s*(?:BAB\s+V)\b', re.MULTILINE | re.IGNORECASE),
}

# Penanda ISI PENELITIAN SUNGGUHAN (data/analisis sudah jalan)
_POLA_HASIL = re.compile(
    r'\b(?:hasil\s+penelitian|uji\s+(?:hipotesis|t|f|asumsi)|'
    r'koefisien\s+determinasi|regresi|pembahasan\s+hasil|'
    r'temuan\s+penelitian|triangulasi|koding)\b',
    re.IGNORECASE)


@dataclass
class HasilDeteksi:
    """Hasil deteksi jenis dokumen — SELALU sediakan alasan agar bisa diaudit."""
    jenis: str
    kategori: str
    jenjang: str
    label: str
    yakin: bool                       # False → pemanggil WAJIB tanya user 1x
    skor: dict[str, int] = field(default_factory=dict)
    bukti: list[str] = field(default_factory=list)
    ragu_antara: list[str] = field(default_factory=list)
    standar: Standar | None = None

    @property
    def lolos_akademik(self) -> bool:
        return self.jenis in JENIS_AKADEMIK

    def pesan_ke_user(self) -> str:
        """Kalimat siap tampil. PERNYATAAN kalau yakin, PERTANYAAN kalau ragu."""
        if self.yakin:
            return (f'Wulan mengenali dokumen ini sebagai **{self.label}**. '
                    f'Wulan akan memakai aturan {self.jenjang}. '
                    f'Kalau bukan, tinggal ubah ya.')
        pilihan = ' atau '.join(LABEL_JENIS.get(j, j) for j in self.ragu_antara)
        return (f'Wulan belum yakin dokumen ini {pilihan}. '
                f'Biar Wulan tidak salah aturan, ini menurut Bos yang mana?')


def _bersih(teks: str) -> str:
    return re.sub(r'[ \t]+', ' ', (teks or ''))


def _wilayah_cover(teks: str) -> str:
    """Ambil bagian AWAL naskah = halaman judul/cover.

    Cover adalah bukti TERKUAT karena di situ tertulis kata resmi jenjang
    ("TESIS", "DISERTASI", "SKRIPSI") yang ditetapkan kampus.
    Ambil 2.500 karakter pertama; kalau ada penanda "BAB I" lebih awal, batasi
    di situ (biar tidak tercampur isi).
    """
    potong = 2500
    m = _POLA_BAB['I'].search(teks)
    if m and m.start() < potong:
        potong = m.start()
    return teks[:max(600, potong)]


def _skor_kata(teks: str, kali: int = 1) -> dict[str, int]:
    skor: dict[str, int] = {}
    for jenis, daftar in KATA_KUAT.items():
        total = 0
        for pola, bobot in daftar:
            n = len(re.findall(pola, teks, re.IGNORECASE))
            if n:
                total += bobot * min(n, 3)     # cap 3x supaya tidak dikuasai 1 kata
        if total:
            skor[jenis] = skor.get(jenis, 0) + total * kali
    return skor


def deteksi_struktur(teks: str) -> tuple[str, str]:
    """Tentukan KATEGORI dari struktur bab yang benar-benar ada.

    Kembalikan (kategori, keterangan).
    """
    ada = {k: bool(p.search(teks)) for k, p in _POLA_BAB.items()}
    n_bab = sum(ada.values())
    ada_hasil = bool(_POLA_HASIL.search(teks))

    if n_bab == 0:
        # Tidak ada penanda BAB sama sekali
        if ada_hasil:
            return KAT_LENGKAP, 'tanpa penanda BAB tapi ada isi hasil (gaya artikel)'
        return KAT_UMUM, 'tidak ada struktur bab'
    if not ada['II'] and not ada['III']:
        return KAT_1BAB, f'hanya {[k for k, v in ada.items() if v]}'
    if ada['IV'] or ada['V']:
        return KAT_LENGKAP, f'BAB I-V ({n_bab} bab)'
    # Ada I-III tapi tidak ada IV/V
    if ada_hasil:
        return KAT_LENGKAP, 'BAB I-III + ada isi hasil'
    return KAT_PROPOSAL, 'berhenti di BAB III (usulan)'


def deteksi(teks: str, nama_berkas: str = '') -> HasilDeteksi:
    """Deteksi jenis dokumen dari TEKS naskah. Rp 0 — tanpa AI.

    Berlapis & berbobot:
      (1) COVER (x3)   — bukti terkuat, kata resmi kampus
      (2) SELURUH teks (x1)
      (3) struktur bab → kategori
      (4) nama berkas   — bukti tambahan
    """
    if not teks or len(teks.strip()) < 80:
        return HasilDeteksi(
            jenis=JENIS_UMUM, kategori=KAT_UMUM, jenjang='—',
            label=LABEL_JENIS[JENIS_UMUM], yakin=False,
            bukti=['teks terlalu pendek untuk dikenali'],
            ragu_antara=[JENIS_SKRIPSI, JENIS_TESIS, JENIS_UMUM],
            standar=STANDAR[JENIS_UMUM])

    t = _bersih(teks)
    skor: dict[str, int] = {}

    # (1) COVER — bobot x3
    cover = _wilayah_cover(t)
    for k, v in _skor_kata(cover, kali=3).items():
        skor[k] = skor.get(k, 0) + v

    # (2) SELURUH teks — bobot x1
    for k, v in _skor_kata(t).items():
        skor[k] = skor.get(k, 0) + v

    # (4) Nama berkas — bobot x3 (user sering menamai "Tesis_Bab1.docx")
    if nama_berkas:
        nb = re.sub(r'[_\-\.]', ' ', nama_berkas)
        for k, v in _skor_kata(nb, kali=3).items():
            skor[k] = skor.get(k, 0) + v

    kategori, ket_struktur = deteksi_struktur(t)

    # Aturan keras: kalau struktur jelas "dokumen umum" DAN skor akademik lemah
    # → jangan paksa jadi akademik (BAHAYA: nota diperlakukan sebagai skripsi).
    skor_akademik = sum(skor.get(j, 0) for j in JENIS_AKADEMIK)
    if kategori == KAT_UMUM and skor_akademik < 8:
        return HasilDeteksi(
            jenis=JENIS_UMUM, kategori=KAT_UMUM, jenjang='—',
            label=LABEL_JENIS[JENIS_UMUM], yakin=True, skor=skor,
            bukti=[f'struktur: {ket_struktur}',
                   f'skor akademik lemah ({skor_akademik})'],
            standar=STANDAR[JENIS_UMUM])

    if not skor:
        return HasilDeteksi(
            jenis=JENIS_UMUM, kategori=kategori, jenjang='—',
            label=LABEL_JENIS[JENIS_UMUM], yakin=False, skor=skor,
            bukti=[f'struktur: {ket_struktur}', 'tidak ada kata kunci jenjang'],
            ragu_antara=[JENIS_SKRIPSI, JENIS_TESIS, JENIS_UMUM],
            standar=STANDAR[JENIS_UMUM])

    urut = sorted(skor.items(), key=lambda x: -x[1])
    jenis_menang, skor_menang = urut[0]
    skor_kedua = urut[1][1] if len(urut) > 1 else 0

    # Bukti untuk audit (supaya bisa dipertanggungjawabkan ke user)
    bukti: list[str] = [f'struktur: {ket_struktur}']
    for jenis, nilai in urut[:3]:
        bukti.append(f'skor {LABEL_JENIS[jenis]} = {nilai}')
    if nama_berkas:
        bukti.append(f'nama berkas: {nama_berkas}')

    # ── Aturan keyakinan (KRUSIAL: salah jenjang = naskah rusak) ──────────
    # (a) menang TELAK: skor tertinggi >= 10 dan >= 2x skor kedua
    telak = skor_menang >= 10 and skor_menang >= 2 * max(skor_kedua, 1)
    # (b) menang jelas tanpa lawan berarti
    jelas = skor_menang >= 10 and skor_kedua <= skor_menang * 0.5
    yakin = telak or jelas

    # (c) PROPOSAL: kalau struktur bilang proposal, dan jenis terdeteksi juga
    #     akademik → proposal menang (kategori memberi tahu tahapnya).
    if kategori == KAT_PROPOSAL and jenis_menang in JENIS_AKADEMIK:
        if skor.get(JENIS_PROPOSAL, 0) >= 8:
            jenis_menang = JENIS_PROPOSAL

    # (d) kategori 1bab: jangan turunkan jadi proposal/dokumen umum bila ada
    #     kata jenjang kuat — user memang cuma mengunggah 1 bab.
    ragu: list[str] = []
    if not yakin:
        ragu = [j for j, _ in urut[:3]]
        if JENIS_UMUM not in ragu and skor_akademik < 12:
            ragu.append(JENIS_UMUM)

    # 'proposal' bukan "jenjang" — jenjangnya tetap ikut naskah. Untuk proposal
    # kita laporkan jenjang TIDAK DIKETAHUI agar AI tidak salah standar.
    jenjang = (STANDAR[jenis_menang].jenjang_resmi
               if jenis_menang in STANDAR else '—')

    return HasilDeteksi(
        jenis=jenis_menang, kategori=kategori, jenjang=jenjang,
        label=LABEL_JENIS[jenis_menang], yakin=yakin, skor=skor,
        bukti=bukti, ragu_antara=ragu, standar=STANDAR.get(jenis_menang))


def deteksi_dari_brief(brief: dict | None) -> HasilDeteksi | None:
    """Kalau Brief sudah punya `jenis` terisi (sistem/user), pakai itu."""
    if not isinstance(brief, dict):
        return None
    j = brief.get('jenis')
    if j in STANDAR:
        kat = brief.get('kategori') or KAT_LENGKAP
        return HasilDeteksi(
            jenis=j, kategori=kat,
            jenjang=(brief.get('jenjang') or STANDAR[j].jenjang_resmi),
            label=LABEL_JENIS[j], yakin=True,
            bukti=['dari Research Brief'], standar=STANDAR[j])
    return None


def blok_prompt(h: HasilDeteksi) -> str:
    """Blok teks SIAP SISIP ke prompt AI.

    Ini yang membuat prompt jadi TAJAM: AI tidak lagi menebak jenjang, dan
    tahu aturan mana yang berlaku (hipotesis maksimum, keharusan novelty, dst.).
    Rp 0 — murni penyusunan teks.
    """
    s = h.standar
    baris = [
        '== JENIS DOKUMEN (hasil deteksi sistem — PAKAI, jangan tebak ulang) ==',
        f'Jenis      : {h.label}',
        f'Kategori   : {h.kategori}',
        f'Jenjang    : {h.jenjang}',
        f'Keyakinan  : {"TINGGI" if h.yakin else "RENDAH — perlu konfirmasi user"}',
    ]
    if not h.yakin and h.ragu_antara:
        baris.append('Kemungkinan lain: '
                     + ', '.join(LABEL_JENIS.get(x, x) for x in h.ragu_antara))
    if h.bukti:
        baris.append('Bukti: ' + ' · '.join(h.bukti[:4]))

    if s:
        baris += [
            '',
            '== ATURAN WAJIB UNTUK JENIS INI (pelanggaran = revisi SALAH) ==',
            f'• Hipotesis  : {s.hipotesis_min}–{s.hipotesis_maks} hipotesis '
            f'(JANGAN pangkas bila jumlahnya masih dalam rentang ini)',
            f'• Novelty    : {"WAJIB ada temuan baru" if s.wajib_novelty else "tidak dituntut"}',
            f'• Kontribusi teori: {"WAJIB" if s.wajib_kontribusi_teori else "tidak dituntut"}',
            f'• Kedalaman  : {s.kedalaman_pembahasan}',
            f'• Catatan    : {s.catatan}',
        ]

    if h.jenis == JENIS_UMUM:
        baris += [
            '',
            '== JALUR KHUSUS NON-AKADEMIK (KRUSIAL) ==',
            'Dokumen ini BUKAN naskah akademik. DILARANG:',
            '• memaksakan struktur BAB I–V',
            '• menambah hipotesis / tinjauan pustaka / sitasi APA',
            '• memakai bahasa "penelitian ini menguji…"',
            'YANG DIBENAHI: kejelasan maksud, tata bahasa, kelengkapan unsur '
            'dokumen, konsistensi nama/tanggal/nominal/pihak.',
        ]
    elif h.jenis == JENIS_PROPOSAL:
        baris += [
            '',
            '== TAHAP PROPOSAL (KRUSIAL) ==',
            'Naskah ini USULAN — datanya belum dikumpulkan. DILARANG:',
            '• mengarang temuan, angka hasil, atau pembahasan hasil',
            '• menulis "hasil penelitian menunjukkan…"',
            'Kalau komentar pembimbing meminta data hasil → jawab jujur bahwa '
            'data belum ada, sebutkan apa yang perlu dikumpulkan dulu.',
        ]
    elif h.kategori == KAT_1BAB:
        baris += [
            '',
            '== NASKAH SEBAGIAN (hanya 1 bab) ==',
            'Jangan menuntut kelengkapan 5 bab. Revisi sesuai bab yang ada saja. '
            'Pastikan lonceng/rujukan ke bab lain tidak menyesatkan.',
        ]
    return '\n'.join(baris)
