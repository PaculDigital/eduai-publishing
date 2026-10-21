"""Publish Buku — daftar jenis buku (5 kartu).

═══════════════════════════════════════════════════════════════════════════
KENAPA BERKAS INI ADA (putusan Bos 17 Okt 2026)
═══════════════════════════════════════════════════════════════════════════
Fitur "Publish Buku" = 5 kartu jenis buku di halaman /buku. Bos memutuskan:
    · desain = A (kartu bergambar)
    · 5 kartu: Buku Ajar · Buku Umum · Buku Monograf · Book Chapter ·
               Buku Referensi
    · Buku Referensi input FLEKSIBEL (tema bebas ATAU bahan sendiri)

PRINSIP BOS: "jangan buat baru tapi lebih optimal kan yang sudah ada".
⇒ Berkas ini TIDAK berisi mesin produksi buku. Mesinnya SUDAH ADA dan
  dipakai ulang apa adanya:

    buku-ajar-obe   → /opt/data/bcp_full_pipeline.py
                      /opt/data/bcp_phase3_visual.py
    buku-umum       → /opt/data/buku_umum_pipeline.py
                      /opt/data/buku_umum_assembly.py
    buku-monograf   → pipeline 5 tahap (skill buku-monograf)
    book-chapter    → /opt/data/scripts/book_chapter_pipeline.py
    buku-referensi  → BELUM ADA skill ⇒ `siap: False` (tombol "Segera")

═══════════════════════════════════════════════════════════════════════════
YANG PERLU DIBANGUN NANTI (BUKAN sekarang — tunggu perintah Bos)
═══════════════════════════════════════════════════════════════════════════
  · `POST /buku/mulai` → buat Berkas/Dokumen dengan jenis buku terpilih
  · jalankan pipeline sesuai `mesin` di bawah
  · potong kuota lewat `kuota.potong_banyak()` (SUDAH ADA, jangan dompet baru)
"""
from __future__ import annotations

#  ══════════════════════════════════════════════════════════════════════════
#  DAFTAR JENIS BUKU — SATU SUMBER
#  ══════════════════════════════════════════════════════════════════════════
#  Field:
#    kode     : id stabil (dipakai form & pipeline). JANGAN diubah sembarangan.
#    nama     : nama yang dilihat user.
#    label    : baris kecil di bawah nama (huruf kapital).
#    ikon     : WAJIB nama yang ADA di app/static/ikon/lucide.svg.
#               Diperiksa 17 Okt 2026: book-open, graduation-cap, file-text,
#               clipboard-check, list — semua ADA. Jangan mengarang nama.
#    tanya    : pertanyaan pemandu (bahasa user, bukan bahasa teknis).
#    isi      : 3 poin ringkas.
#    lencana  : teks lencana kiri-bawah.
#    warna    : hijau | biru | kuning | abu  (kelas CSS `.l-<warna>`).
#    siap     : True = tombol "Mulai" aktif · False = tombol "Segera".
#    sumber   : apa yang harus disiapkan user (untuk nanti di /buku/mulai).
#    mesin    : berkas pipeline yang dipakai (dokumentasi, bukan import).
#    skill    : nama skill terkait (dokumentasi + cek ketersediaan).
#  ⚠️ URUTAN = urutan tampil di layar. Jangan acak.
JENIS_BUKU = [
    {
        'kode': 'buku-ajar',
        'nama': 'Buku Ajar',
        'label': 'BERBASIS RPS · OBE',
        'ikon': 'graduation-cap',
        'tanya': 'Punya RPS mata kuliah? Jadi buku ajar lengkap.',
        'isi': ['Tujuan pembelajaran (TIU/TIK)',
                'Latihan + checklist tiap bab',
                'Siap cetak A5'],
        'lencana': 'Perlu RPS',
        'warna': 'hijau',
        'siap': True,
        'sumber': ['rps'],
        'mesin': 'bcp_full_pipeline.py + bcp_phase3_visual.py',
        'skill': 'buku-ajar-obe',
    },
    {
        'kode': 'buku-umum',
        'nama': 'Buku Umum',
        'label': 'NON-FIKSI · NARATIF',
        'ikon': 'book-open',
        'tanya': 'Mau tulis buku yang enak dibaca siapa saja?',
        'isi': ['Hukum, ekonomi, bisnis, psikologi',
                'Tone naratif, tidak kaku',
                'Hook kuat di tiap bab'],
        'lencana': 'Tema bebas',
        'warna': 'biru',
        'siap': True,
        'sumber': ['tema'],
        'mesin': 'buku_umum_pipeline.py + buku_umum_assembly.py',
        'skill': 'buku-umum',
    },
    {
        'kode': 'buku-monograf',
        'nama': 'Buku Monograf',
        'label': 'HASIL PENELITIAN',
        'ikon': 'clipboard-check',
        'tanya': 'Punya skripsi/tesis yang mau jadi buku?',
        'isi': ['Analisis novelty 5 lapis',
                'Debat pro-kontra akademik',
                'A5 · 150–180 halaman'],
        'lencana': 'Perlu naskah',
        'warna': 'kuning',
        'siap': True,
        'sumber': ['naskah_penelitian'],
        'mesin': 'pipeline 5 tahap monograf',
        'skill': 'buku-monograf',
    },
    {
        'kode': 'book-chapter',
        'nama': 'Book Chapter',
        'label': 'SATU BAB · ANTOLOGI',
        'ikon': 'file-text',
        'tanya': 'Ikut buku kolaborasi? Cukup satu bab.',
        'isi': ['1 bab utuh siap terbit',
                '8 referensi terverifikasi',
                'Diagram otomatis'],
        'lencana': 'Perlu judul bab',
        'warna': 'biru',
        'siap': True,
        'sumber': ['judul_bab'],
        'mesin': 'scripts/book_chapter_pipeline.py',
        'skill': 'book-chapter',
    },
    {
        'kode': 'buku-referensi',
        'nama': 'Buku Referensi',
        'label': 'KUMPULAN TEORI',
        'ikon': 'list',
        'tanya': 'Butuh buku rujukan teori & konsep?',
        'isi': ['Teori + definisi dari sumber nyata',
                'Sitasi padat (minimal 15 per bab)',
                'Tema bebas atau bahan sendiri'],
        'lencana': 'Segera',
        'warna': 'kuning',
        #  ⚠️ BELUM ADA skill `buku-referensi` (diperiksa 17 Okt 2026).
        #     JANGAN diubah jadi True sebelum skill + mesinnya benar-benar ada
        #     dan teruji — tombol yang menjanjikan fitur kosong = janji palsu.
        'siap': False,
        'sumber': ['tema', 'bahan_sendiri'],
        'mesin': '(belum ada — rencana: sambung buku_umum_pipeline + prompt teori)',
        'skill': 'buku-referensi',
    },
]


#  ══════════════════════════════════════════════════════════════════════════
#  BUKU UMUM — BIDANG + UNTUK SIAPA (putusan Bos 18 Okt 2026)
#  ══════════════════════════════════════════════════════════════════════════
#  Bos (verbatim): "Memang di menu buku umum belum ada pilihan bidang dan
#  jenis nya? Untuk profesional atau untuk anak-anak?"
#  ⇒ HANYA kartu Buku Umum yang berubah. Kartu lain TIDAK disentuh.
#
#  Dua jawaban ini menentukan SELURUH wajah buku lewat `/opt/data/jenis_buku.py`
#  dan `/opt/data/tone_menulis.py`:
#    · ilustrasi (style block gambar AI)
#    · infografis (palet, bentuk label, font)
#    · cara menulis (panjang kalimat, sapaan, sitasi)
#
#  ⚠️ `kode_jenis` WAJIB cocok dengan kunci di jenis_buku.PAKET.
#     Gerbang `gerbang_menu_buku_umum.py` memeriksa kecocokan ini.
BIDANG_UMUM = [
    {'kode': 'hukum', 'nama': 'Hukum'},
    {'kode': 'ekonomi', 'nama': 'Ekonomi'},
    {'kode': 'bisnis', 'nama': 'Bisnis'},
    {'kode': 'psikologi', 'nama': 'Psikologi'},
    {'kode': 'pendidikan', 'nama': 'Pendidikan'},
    {'kode': 'sosial', 'nama': 'Sosial'},
    {'kode': 'kesehatan', 'nama': 'Kesehatan'},
    {'kode': 'teknologi', 'nama': 'Teknologi'},
]

UNTUK_SIAPA = [
    {
        'kode': 'profesional',
        'kode_jenis': 'umum',
        'nama': 'Profesional',
        'ket': 'Dewasa — bisnis, hukum, ekonomi, kebijakan',
        # ⚠️ Ikon WAJIB ada di app/static/ikon/lucide.svg (diperiksa 18 Okt 2026).
        #    'briefcase' TIDAK ADA — jangan tulis dari ingatan.
        'ikon': 'wallet',
    },
    {
        'kode': 'anak',
        'kode_jenis': 'anak',
        'nama': 'Anak-anak',
        'ket': 'Usia 4–10 tahun, banyak gambar, bahasa sederhana',
        # 'smile' TIDAK ADA di sprite — pakai 'sparkles' (ada).
        'ikon': 'sparkles',
    },
    {
        'kode': 'pelajar',
        'kode_jenis': 'pendidikan',
        'nama': 'Pelajar',
        'ket': 'SD–SMP, buku penunjang pelajaran',
        'ikon': 'graduation-cap',
    },
]


def cari_untuk_siapa(kode: str) -> dict | None:
    for u in UNTUK_SIAPA:
        if u['kode'] == kode:
            return u
    return None


def jenis_gaya(bidang: str, untuk: str) -> str:
    """Tentukan kunci paket gaya (`jenis_buku.PAKET`) dari 2 pilihan user.

    Raise ValueError kalau pilihan tidak dikenal — JANGAN fallback diam-diam,
    user yang memilih "anak" tapi dapat gaya dewasa tidak akan sadar salah.
    """
    u = cari_untuk_siapa(untuk)
    if not u:
        raise ValueError(f"pilihan 'untuk siapa' tidak dikenal: {untuk}")
    if not any(b['kode'] == bidang for b in BIDANG_UMUM):
        raise ValueError(f"bidang tidak dikenal: {bidang}")
    return u['kode_jenis']


def semua() -> list[dict]:
    """Daftar jenis buku untuk template /buku (urutan tetap)."""
    return JENIS_BUKU


def cari(kode: str) -> dict | None:
    """Ambil satu jenis berdasarkan kode; None kalau tidak ada."""
    for b in JENIS_BUKU:
        if b['kode'] == kode:
            return b
    return None


def id_dokumen(kode_kartu: str) -> str:
    """ID DOKUMEN untuk buku ini — dipakai memilih alat (Jev/Hakim/mutu buku).

    ACC Bos 19 Okt 2026: "harus punya id sendiri ... agar menggunakan jev dan
    hakim tepat dan tidak salah alat".

    Kartu di layar memakai STRIP ('buku-umum'), identitas di `app/jenis.py`
    memakai GARIS BAWAH ('buku_umum'). Perbedaan ini SATU-SATUNYA tempat
    penerjemahannya — supaya tidak ada dua kebenaran.

    ID tak dikenal → '' (pemanggil WAJIB menolak, jangan menebak).
    """
    from .jenis import JENIS_BUKU as _ID
    kandidat = (kode_kartu or '').strip().replace('-', '_')
    return kandidat if kandidat in _ID else ''


def siap(kode: str) -> bool:
    """True kalau jenis ini boleh dijalankan sekarang."""
    b = cari(kode)
    return bool(b and b.get('siap'))
