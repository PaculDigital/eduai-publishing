"""Konfigurasi EduAi Publishing — single source of truth.

Semua nilai sensitif dari environment, TIDAK di-hardcode.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv('EDUAI_DATA_DIR', BASE_DIR / 'data'))
UPLOAD_DIR = Path(os.getenv('EDUAI_UPLOAD_DIR', BASE_DIR / 'uploads'))

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- database ---
DB_PATH = DATA_DIR / 'eduai.db'
DATABASE_URL = f'sqlite:///{DB_PATH}'

# --- keamanan ---
SECRET_KEY = os.getenv('EDUAI_SECRET_KEY', '')
if not SECRET_KEY:
    raise RuntimeError(
        'EDUAI_SECRET_KEY belum diset. Jalankan container dengan env_file yang memuat secret.'
    )

SESSION_COOKIE = 'eduai_session'
SESSION_MAX_AGE = 60 * 60 * 24 * 7          # 7 hari

# --- paket kuota (sumber tunggal; landing page & backend harus sama) ---
PAKET = {
    'gratis':   {'nama': 'Gratis',   'mb': 30,    'harga': 0,       'label': 'Gratis'},
    'penulis':  {'nama': 'Penulis',  'mb': 100,   'harga': 50_000,  'label': 'Rp 50.000'},
    'peneliti': {'nama': 'Peneliti', 'mb': 300,   'harga': 100_000, 'label': 'Rp 100.000'},
    'penerbit': {'nama': 'Penerbit', 'mb': 1024,  'harga': 300_000, 'label': 'Rp 300.000'},
}
KUOTA_DEFAULT_MB = PAKET['gratis']['mb']

# --- batas unggah ---
# Batas ukuran PER BERKAS (ACC Bos 15Sep26 (2): 5 MB → **15 MB**).
# DASAR AKTUAL (diukur 15Sep26 atas 2 dokumen NYATA Bos):
#   - Skripsi Wulandari FULL = 7,29 MB  → TAPI 6,83 MB (94%) adalah GAMBAR!
#     Teks yang benar-benar dibaca AI cuma 0,46 MB (700.599 karakter).
#   - Tesis Bos (s/d BAB III)  = 0,56 MB → teks 63.797 karakter.
# KESIMPULAN: mahasiswa dengan banyak gambar (lampiran/dokumentasi) TIDAK
# boleh ditolak hanya karena file besar — AI tidak membaca gambarnya.
# Karena itu 15 MB = kompromi: cukup untuk skripsi bergambar, sementara
# teks maksimumnya (~1,5 juta karakter) masih SANGGUP dibaca model combo
# (uji 15Sep26: AI baca 1.499.840 karakter / 250.454 token / 7,6 detik).
# ⚠️ JANGAN ubah angka ini tanpa cek kemampuan combo (9router).
MAX_UPLOAD_BYTES = 15 * 1024 * 1024         # 15 MB per file
EKSTENSI_DIIZINKAN = {
    #  ── PUTUSAN BOS 10 Okt 2026 (pilihan "B" lalu "A") ──────────────────────
    #  FORMAT LAMA OFFICE (.doc/.xls/.ppt) DILARANG — alasan Bos: "agar standard
    #  aplikasi. Jika user upload .doc diminta ganti menjadi .docx terlebih
    #  dahulu." Yang lama (biner OLE) juga bisa memuat MAKRO dan tidak bisa
    #  dibaca alat kita dengan aman.
    #  ⇒ Yang sah hanya format BARU (OOXML): .docx/.xlsx/.pptx.
    '.docx', '.pdf', '.xlsx', '.pptx',
    '.txt', '.rtf', '.odt', '.ods', '.odp', '.csv', '.png', '.jpg', '.jpeg', '.zip',
}

#  Ekstensi format LAMA Office yang DITOLAK + pesan gantinya (dipakai pintu unggah).
EKSTENSI_LAMA = {
    '.doc': '.docx',
    '.xls': '.xlsx',
    '.ppt': '.pptx',
    '.dot': '.docx',
    '.dotx': '.docx',
    '.dotm': '.docx',
    '.docm': '.docx',
    '.xlsm': '.xlsx',
    '.pptm': '.pptx',
}

# --- batas per user (permintaan Bos 12Sep26) ---
# Kenapa JUMLAH file dibatasi juga, bukan hanya MB: tanpa batas jumlah,
# user bisa unggah ratusan file kecil -> inode disk penuh walau MB masih sisa.
MAX_FILE_USER = int(os.getenv('EDUAI_MAX_FILE_USER', '50'))

# Kenapa sesi edit dibatasi: tiap dokumen yang dibuka OnlyOffice menahan
# 1 proses editor + cache .bin + 1 koneksi WebSocket. 1 user buka 5 dokumen
# = 5x beban CPU/RAM di VPS. Batas 3 supaya VPS aman saat banyak user.
MAX_SESI_EDIT = int(os.getenv('EDUAI_MAX_SESI_EDIT', '3'))

# Sesi yang tidak mengirim heartbeat selama ini dianggap BASI -> auto-tutup.
SESI_IDLE_MENIT = int(os.getenv('EDUAI_SESI_IDLE_MENIT', '5'))

# --- OnlyOffice ---
OO_URL = os.getenv('EDUAI_OO_URL', '')           # mis. http://172.17.0.7
OO_JWT_SECRET = os.getenv('EDUAI_OO_JWT_SECRET', '')
# URL editor yang dimuat BROWSER (lewat Cloudflare Tunnel, rute /oo)
OO_PUBLIC_URL = os.getenv('EDUAI_OO_PUBLIC_URL',
                          'https://eduai.bikinaja.id/oo/aset')
PUBLIC_BASE_URL = os.getenv('EDUAI_PUBLIC_BASE_URL', 'https://eduai.bikinaja.id')

# --- admin ---
ADMIN_EMAIL = os.getenv('EDUAI_ADMIN_EMAIL', 'eduai@bikinaja.id')

# --- Pakasir QRIS (dipakai ulang dari project wa-marketing) ---
# Nilai sensitif HANYA dari environment — JANGAN di-hardcode di kode.
PAKASIR_SLUG = os.getenv('PAKASIR_SLUG', '')
PAKASIR_API_KEY = os.getenv('PAKASIR_API_KEY', '')
PAKASIR_SANDBOX = os.getenv('PAKASIR_SANDBOX', 'true').lower() in ('1', 'true', 'yes')

# Batas waktu QRIS (detik). Pakasir memberi ~15 menit; kita pakai 20 menit
# sebagai ambang "kedaluwarsa" di sisi aplikasi.
QRIS_EXPIRE_MENIT = 20

# 12Sep26: batas transaksi MENUNGGU (pending) serentak per user.
# KENAPA dibatasi: tanpa batas, user bisa membuat puluhan QRIS di Pakasir
# sekaligus -> boros, riwayat penuh sampah, dan berisiko kena rate-limit.
# Angka 3 = sama dengan MAX_SESI_EDIT supaya konsisten & mudah diingat.
MAX_PENDING = int(os.getenv('EDUAI_MAX_PENDING', '3'))


# ── Cloudflare Access (untuk akses oo.bikinaja.id) ──────────────────
# Subdomain oo.bikinaja.id dilindungi Cloudflare Access: manusia DITOLAK,
# hanya yang membawa service token yang lolos.
CF_ACCESS_ID = os.getenv('EDUAI_OO_CF_ACCESS_ID', '')
CF_ACCESS_SECRET = os.getenv('EDUAI_OO_CF_ACCESS_SECRET', '')

# ── Proxy AI (/api/ai/v1) — 13Sep26 langkah #2 ─────────────────────
# Arsitektur FINAL (ACC Bos 13Sep26): app memanggil COMBO `EduAi` di
# 9router; urutan model & fallback diatur Bos dari panel 9router.
ROUTER_BASE = os.getenv('EDUAI_ROUTER_BASE', 'http://172.17.0.1:20128/v1')
ROUTER_KEY = os.getenv('EDUAI_ROUTER_KEY', '')
if not ROUTER_KEY:
    raise RuntimeError(
        'EDUAI_ROUTER_KEY belum diset. Jalankan container dengan env '
        'EDUAI_ROUTER_KEY (key 9router khusus EduAi).'
    )
AI_MODEL = os.getenv('EDUAI_AI_MODEL', 'EduAi')
AI_TIMEOUT_DETIK = float(os.getenv('EDUAI_AI_TIMEOUT', '420'))

# ══ C6 (25Sep26) — BATAS SABAR jalur 1 sebelum pindah jalur 2 ═══════════
#  AKAR MASALAH (terbaca dari kode, bukan dugaan):
#      `_panggil_router()` hanya memindahkan ke jalur 2 (OpenRouter) kalau
#      jalur 1 melempar GALAT. Kalau jalur 1 NYANGKUT (lambat), tidak ada
#      yang memindahkan → mahasiswa menunggu AI_TIMEOUT_DETIK (420 dtk /
#      7 MENIT) lalu dapat "Layanan AI tidak tersedia", padahal OpenRouter
#      sehat dan bisa menjawab.
#
#  PAGAR: kalau jalur 1 belum juga menjawab dalam BATAS SABAR, MENYERAH dan
#  pindah ke jalur 2 — sisa waktu tetap dihormati.
#
#  ANGKA 90 DIPILIH DARI DATA NYATA + PUTUSAN BOS (29Sep26, ditegaskan
#  05Okt26 "Buat semua sabar jadi 90 saja semua"):
#  · Dengan `enable_thinking:False` di KEDUA jalur (Opsi Dua-duanya), proses
#    revisi yang sehat turun drastis: terukur 3/3 panggilan 7,9–10,3 dtk,
#    dan presisi 4/4 komentar terjawab tanpa meluap ke tetangga.
#  · Proses seberat apa pun kini jauh di bawah 90 dtk, jadi batas sabar 90
#    TIDAK membunuh proses sehat — sebaliknya membuat mahasiswa cepat
#    dipindahkan ke jalur 2 kalau jalur 1 nyangkut.
#  · 90 < 420 (AI_TIMEOUT_DETIK) → sisa waktu tetap cukup untuk jalur 2.
#  ⚠️ Kalau suatu saat `enable_thinking` dinyalakan lagi, angka ini WAJIB
#     ditinjau ulang (thinking membuat proses kembali 74–562 dtk).
BATAS_SABAR_JALUR1 = float(os.getenv('EDUAI_AI_SABAR', '90'))
AI_MAX_NASKAH_KARAKTER = int(os.getenv('EDUAI_AI_MAX_NASKAH', '60000'))
AI_MAX_KOMENTAR = int(os.getenv('EDUAI_AI_MAX_KOMENTAR', '10'))

# ── FALLBACK INTERNAL BERBAYAR (ACC Bos 17Sep26) ─────────────────────────
# KENAPA ADA (kekhawatiran Bos, benar): 9router punya fallback ANTAR-provider
# farming (gratis), TAPI kalau **9router sendiri** down / semua provider
# farming tumbang bersamaan, app kehilangan jalur → user gagal.
# Ini = JALUR KEDUA langsung ke OpenRouter (berbayar, murah, andal).
#
# Model: `inclusionai/ling-3.0-flash` — ctx 262.144 token,
#   $0,000000021/token masuk · $0,000000063/token keluar (UJI NYATA 17Sep26:
#   naskah 4.788 token → 2,1 dtk, jawaban benar; TIDAK ada versi `:free`).
# `provider.only=[novita] + allow_fallbacks=false` = patuh contoh Bos.
FALLBACK_BASE = os.getenv('EDUAI_FALLBACK_BASE', '')
FALLBACK_KEY = os.getenv('EDUAI_FALLBACK_KEY', '')
FALLBACK_MODEL = os.getenv('EDUAI_FALLBACK_MODEL', 'inclusionai/ling-3.0-flash-fin:free')
FALLBACK_MODEL_2 = os.getenv('EDUAI_FALLBACK_MODEL_2', '')
FALLBACK_MODEL_3 = os.getenv('EDUAI_FALLBACK_MODEL_3', '')
FALLBACK_MODEL_4 = os.getenv('EDUAI_FALLBACK_MODEL_4', '')
FALLBACK_PROVIDER = os.getenv('EDUAI_FALLBACK_PROVIDER', 'novita')
FALLBACK_MODEL_4_PROVIDER = os.getenv('EDUAI_FALLBACK_MODEL_4_PROVIDER', 'alibaba')
FALLBACK_AKTIF = bool(FALLBACK_BASE and FALLBACK_KEY)


def daftar_fallback() -> list[tuple[str, str]]:
    """Urutan model fallback OpenRouter → [(model, provider), …].

    GRATIS dulu, berbayar murah, lalu paling akhir.
    UJI NYATA 17Sep26 (semua patuh format `[PROFIL]`):
      ling-3.0-flash-fin:free   → 7,6 dtk · 6.229 kar   ← TERPANJANG
      ling-3.0-flash-sante:free → 7,3 dtk · 2.116 kar   ← cadangan
      ling-3.0-flash            → 1,0 dtk · berbayar murah (ling)
      qwen/qwen3.7-flash        → 42,4 dtk · ctx 1.000.000 (ACC Bos 17Sep26)
                                   HANYA provider `alibaba`

    ⚠️ Tiap model boleh punya PROVIDER SENDIRI: `qwen3.7-flash` HANYA dilayani
    `alibaba`; keluarga `ling` dilayani `novita`. Kalau provider dipaksa sama,
    OpenRouter balas 404 "No allowed providers are available".
    ⚠️ `qwen3.7-flash` GANTI `openai/gpt-oss-20b` (ACC Bos 17Sep26) karena
    KONTEKS 1.000.000 vs 131.072 token, dengan HARGA SAMA PERSIS.
    """
    pasangan = [
        (FALLBACK_MODEL, FALLBACK_PROVIDER),
        (FALLBACK_MODEL_2, FALLBACK_PROVIDER),
        (FALLBACK_MODEL_3, FALLBACK_PROVIDER),
        (FALLBACK_MODEL_4, FALLBACK_MODEL_4_PROVIDER),
    ]
    return [(m, p) for m, p in pasangan if m]

# ── BATAS TOKEN JAWABAN AI (ACC Bos 16Sep26) ────────────────────────────
# KENAPA ADA: model reasoning (deepseek/gemini "flash") memakai SATU ember
# token untuk BERPIKIR (reasoning_tokens) dan MENJAWAB (content). Kalau
# embernya habis di tahap berpikir, jawaban = KOSONG ("model diam").
# UJI NYATA 16Sep26 (naskah dijalur produksi, combo EduAi):
#   - paragraf pendek  216 kar → reasoning 1.276  → finish=stop    ✅
#   - naskah 15.000 kar       → reasoning 8.000  → finish=length  ❌ KOSONG
#   - naskah 55.000 kar       → reasoning 8.000  → finish=length  ❌ KOSONG
# Jadi 8.000 TIDAK CUKUP untuk naskah ≥15.000 kar. Dinaikkan ke 32.000.
# BIAYA TIDAK MEMBENGKAK: Token Revisi dihitung dari token NYATA
# (lihat TOKEN_REVISI_PER di bawah) — makin banyak token, makin banyak
# Token Revisi yang dibayar user. Jadi TIDAK perlu membatasi AI.
AI_MAX_TOKENS = int(os.getenv('EDUAI_AI_MAX_TOKENS', '32000'))

# ── RUMUS TOKEN REVISI — MASTER_PLAN §4.13 (ACC Bos 15Sep26, DIPASANG 16Sep26)
# Token Revisi = ceil((token_in + token_out) / 10.000) × pengali, cap 60.
# Dihitung SERVER dari token NYATA yang dilaporkan model (bukan tebakan).
# Contoh: 1.500 tok → 1 Token Revisi · 18.000 tok → 2 · 23.000 tok → 3.
# KENAPA pembagi 10.000: sudah dibandingkan 5rb/10rb/15rb/25rb (16Sep26);
# 5.000 bikin skripsi full = 71 Token Revisi (menakutkan user).
TOKEN_REVISI_PER = int(os.getenv('EDUAI_TOKEN_REVISI_PER', '10000'))
TOKEN_REVISI_CAP = int(os.getenv('EDUAI_TOKEN_REVISI_CAP', '60'))

#  ── KERANGKA PER BAB (26Sep26) ──────────────────────────────────────────
#  Satu BAB = 15 Token Revisi. Alasan (arahan Bos): satu bab memerlukan
#  MENCARI SITASI & ARTIKEL sesuai tema+judul, MENYUSUN KERANGKA, dan
#  MEMBUAT TABEL & GRAFIK di dalamnya — jauh lebih berat dari 1 revisi biasa.
#  ⚠️ SATU SUMBER: jangan tulis angka ini di JS/template (pelajaran MAXMB
#     15Sep26: batas ditulis 2 tempat → yang satu tak pernah tersentuh).
#  ⭐ HARGA TOKEN PER BAB (ACC Bos 26Sep26, TERKUNCI) ─────────────────────
#  Bos: "Tiap bab punya pemotongan saldo berbeda, karena beda penanganan dan
#  cara kerja." Angka mengikuti BOBOT KERJA TERUKUR (app/kerangka_bab.py):
#     BAB I   13,0 (ringan: tanpa tabel/grafik)
#     BAB II  19,5 (teori + penelitian terdahulu + 1 tabel + 1 grafik)
#     BAB III 18,5 (2 tabel metode, tanpa grafik)
#     BAB IV  26,5 (TERBERAT: 2 tabel + 2 grafik + hitung data)
#     BAB V   12,5 (ringan: simpulan & saran)
#  ⚠️ BAB IV punya DUA layanan TERPISAH (putusan Bos):
#     'analisa'   → membaca/menafsirkan hasil + narasi pembahasan
#     'olah_data' → mengolah data mentah → tabel/grafik + uji statistik
TOKEN_KERANGKA_BAB: dict[str, int] = {
    '1': int(os.getenv('EDUAI_TOKEN_BAB1', '15')),
    '2': int(os.getenv('EDUAI_TOKEN_BAB2', '20')),
    '3': int(os.getenv('EDUAI_TOKEN_BAB3', '20')),
    '4': int(os.getenv('EDUAI_TOKEN_BAB4', '30')),   # analisa
    '5': int(os.getenv('EDUAI_TOKEN_BAB5', '15')),
    '4:olah_data': int(os.getenv('EDUAI_TOKEN_BAB4_OLAH', '30')),
}


def token_bab(bab: str, layanan: str = 'kerangka') -> int:
    """Harga Token Revisi untuk satu bab (+ layanan khusus).

    `layanan`:
      'kerangka'   → kerangka/naskah bab (default)
      'analisa'    → BAB IV bagian analisa & pembahasan
      'olah_data'  → BAB IV bagian olah data (mesin statistik)
    """
    b = str(bab or '1').strip()
    if layanan == 'olah_data':
        return TOKEN_KERANGKA_BAB.get(f'{b}:olah_data',
                                      TOKEN_KERANGKA_BAB.get(b, 15))
    return TOKEN_KERANGKA_BAB.get(b, 15)

# ── PEMOTONGAN DOKUMEN BESAR (ACC Bos 14Sep26) ──────────────────────────
# Dokumen > AI_POTONG_KARAKTER diproses BERTAHAP. Tiap bagian = 1 revisi.
# Angka 55.000 sengaja di bawah batas 60.000 → ada toleransi 5% (margin
# aman supaya promp/penanda tidak mendorong lewat batas keras).
# Contoh: tesis 64.000 karakter → 2 bagian → 2 revisi (user diberi tahu dulu).
AI_POTONG_KARAKTER = int(os.getenv('EDUAI_AI_POTONG_KARAKTER', '55000'))
AI_POTONG_MAKS_BAGIAN = int(os.getenv('EDUAI_AI_POTONG_MAKS_BAGIAN', '6'))

# ── TONG SAMPAH (ACC Bos 14Sep26) ───────────────────────────────────────
# Berkas yang dihapus user pindah ke Tong Sampah dulu (bukan langsung
# hilang), seperti Google Drive. Hapus permanen otomatis setelah 30 hari.
# Aturan yang disetujui Bos:
#   • lama simpan  = 30 hari
#   • tetap menghitung kuota storage (adil — dorong user bereskan sampah)
#   • hanya user sendiri yang bisa lihat & pulihkan berkasnya
SAMPAH_HARI = int(os.getenv('EDUAI_SAMPAH_HARI', '30'))
# Sebelum hapus permanen, DB di-backup otomatis ke folder ini (di dalam
# container). Bos: "kalau hapus otomatis terbackup".
SAMPAH_BACKUP_DIR = os.getenv('EDUAI_SAMPAH_BACKUP', '/app/data/backup_sampah')
SAMPAH_BACKUP_SIMPAN = int(os.getenv('EDUAI_SAMPAH_BACKUP_SIMPAN', '5'))

# ── ARSIP CATATAN PEMBIMBING (Tahap 3.3, ACC Bos 06Okt26 "A") ───────────
#  Catatan yang SUDAH SELESAI (pembimbing bilang "Sudah oke") dan sudah
#  lewat ARSIP_HARI hari DISEMBUNYIKAN dari daftar utama — tetap tersimpan
#  di DB, hanya terlipat ke bagian "Arsip" supaya daftar tetap segar.
#  ⚠️ HANYA yang SUDAH SELESAI. Catatan yang belum selesai TIDAK PERNAH
#  diarsipkan walau setua apa pun (putusan Bos: jangan sembunyikan yang
#  masih perlu dikerjakan).
ARSIP_HARI = int(os.getenv('EDUAI_ARSIP_HARI', '60'))

# ── KUOTA AI & ADDON — MASTER_PLAN §4.10 (ACC Bos 13Sep26) ──────────────
# ANGKA DI SINI BEKU — jangan diubah tanpa ACC Bos.
# Sumber: MASTER_PLAN §1 + FLAG_LANJUT_DISINI (ACC 13Sep26 11:35).
#
# STRATEGI (jangan dibalik):
#   • PAKET = tiket masuk · ADDON = mesin uang
#   • Kuota habis → tawarkan ADDON, JANGAN dorong upgrade paket
#   • AddOn TERKUNCI untuk paket gratis (validasi di BACKEND)
#   • Reset bulanan tanggal 1, credit HANGUS, lazy (tanpa cron)

# Revisi AI per bulan + akses Mode Belajar + konversi, per paket.
#  URUTAN PAKET (26Sep26) — SATU SUMBER untuk "naik/tidaknya" paket.
#  Dipakai _terapkan_paket_lunas(): beli paket yang lebih tinggi = NAIK,
#  beli paket yang lebih rendah = TIDAK menurunkan paket user.
PAKET_URUT = ['gratis', 'penulis', 'peneliti', 'penerbit']

KUOTA_PAKET = {
    'gratis':   {'revisi': 3,   'belajar_naskah': 0, 'konversi': 0},
    'penulis':  {'revisi': 12,  'belajar_naskah': 0, 'konversi': 0},
    'peneliti': {'revisi': 15,  'belajar_naskah': 1, 'konversi': 1},
    'penerbit': {'revisi': 50,  'belajar_naskah': 2, 'konversi': 2},
}

# ═══════════════════════════════════════════════════════════════════════════
#  PEMBIMBING AI — SAKLAR (ACC Bos 03Okt26)
# ═══════════════════════════════════════════════════════════════════════════
#  Fitur "Periksa dengan AI" di halaman /tinjau (pembimbing).
#
#  ── KENAPA SAKLAR ─────────────────────────────────────────────────────────
#  Pagar 2 dari 4 pagar rencana: kalau ada apa pun yang tidak beres, fitur
#  bisa DIMATIKAN tanpa menyentuh jalur lama (jalur mahasiswa TIDAK
#  bergantung pada fitur ini — fail-safe).
#
#  ⚠️ JANGAN dihapus walau fitur sudah stabil: ini titik henti darurat.
PEMBIMBING_AI_AKTIF = os.environ.get(
    'EDUAI_PEMBIMBING_AI', '1').strip().lower() not in ('0', 'false', 'no', 'off')

#  Batas token untuk pembimbing berpaket `gratis`.
#
#  ── KENAPA ADA (temuan T1, 03Okt26) ───────────────────────────────────────
#  `_member_berbayar()` di ai.py MENOLAK paket `gratis` (gerbang §4.10).
#  Padahal putusan Bos: pembimbing = user paket `gratis` yang dapat 3 token,
#  dan token itu bebas dipakai sebagai mahasiswa ATAU sebagai pembimbing.
#
#  ⇒ Pembimbing berpaket `gratis` DIBUKA **khusus lewat pintu /tinjau**,
#    TIDAK dibuka global (supaya lubang §4.10 tidak terbuka lagi lewat
#    jalan lain). Bebas 2 peran: naskah SENDIRI = mahasiswa, naskah ORANG =
#    pembimbing — dompetnya SATU (`saldo_token`), tidak ada jatah kedua.
#
#  Angka 3 = sama dengan KUOTA_PAKET['gratis']['revisi'] — SATU SUMBER
#  kebenaran; sengaja merujuk ke situ, bukan angka lepas.
PEMBIMBING_GRATIS_TOKEN = KUOTA_PAKET['gratis']['revisi']

# AddOn — hanya untuk paket BERBAYAR (gratis TERKUNCI).
ADDON = {
    'ai':       {'nama': 'Tambah AI',        'harga': 50_000,  'kuota': 30,
                 'satuan': 'revisi', 'keterangan': '+30 revisi AI'},
    'konversi': {'nama': 'Konversi Jurnal',  'harga': 100_000, 'kuota': 1,
                 'satuan': 'dokumen', 'keterangan': '1× konversi ke format jurnal'},
    'publish':  {'nama': 'Publish Jurnal',   'harga': 500_000, 'kuota': 1,
                 'satuan': 'dokumen', 'keterangan': '1× pendampingan publish'},
    'belajar':  {'nama': 'Mode Belajar',     'harga': 75_000,  'kuota': 1,
                 'satuan': 'naskah', 'keterangan': '+1 naskah Mode Belajar'},
    # ── ADDON STORAGE + FOLDER (ACC Bos 15Sep26) ────────────────────────
    # Riwayat/backup revisi + folder ikut memakai kuota storage. Kalau
    # penuh, user ditawari ADDON ini — BUKAN upgrade paket (strategi Bos).
    #
    # SATU AddOn, DUA isi (ACC Bos 15Sep26): +50 MB & +10 folder.
    #   • Terasa murah di mata user → lebih gampang beli.
    #   • Saling mengunci: storage nambah → butuh folder lebih banyak;
    #     folder nambah → butuh storage. Sekali beli, butuh dua-duanya.
    #   • Repeat order → mesin uang (bukan sekali beli lalu selesai).
    #
    # `tambahan` = dict efek ke tiap kuota. Kuncinya HARUS nama kolom asli
    # di model User (`kuota_mb`, `folder_ekstra`) — divalidasi di
    # `kuota.tambah_addon()` yang menolak kolom yang tidak ada.
    'storage':  {'nama': 'Tambah Storage & Folder', 'harga': 25_000,
                 'tambahan': {'kuota_mb': 50, 'folder_ekstra': 10},
                 'satuan': 'paket',
                 'keterangan': '+50 MB storage & +10 folder'},
}

# Paket yang TIDAK boleh membeli AddOn apa pun (validasi di BACKEND).
# ⚠ ACC Bos 15Sep26: user GRATIS tetap TERKUNCI — harus upgrade paket dulu.
#   (Walau merekalah yang paling cepat kehabisan 30 MB, membukanya akan
#    menghapus alasan utama upgrade ke paket berbayar.)
PAKET_TANPA_ADDON = {'gratis'}   # ⚠ alias — jangan diubah tanpa ACC Bos

# Simulasi sidang (Mode Belajar L3) — kuota terpisah, dihitung per tanya-jawab.
KUOTA_SIMULASI_PAKET = {
    'gratis': 0, 'penulis': 0, 'peneliti': 20, 'penerbit': 40,
}

# ── JATAH FOLDER (ACC Bos 15Sep26) ──────────────────────────────────────
# Folder = alat kerapian yang BIKIN user unggah lebih banyak (storage naik =
# untung) SEKALIGUS alasan upgrade tersendiri. None = tak terbatas.
# ⚠ Kalau nanti Bos mau ubah, ubah di sini saja — dipakai backend + UI.
FOLDER_PAKET = {
    'gratis':   3,
    'penulis':  10,
    'peneliti': 25,
    'penerbit': None,        # tak terbatas
}

# Pilihan warna folder (kunci disimpan di DB, teks dipakai UI).
FOLDER_WARNA = {
    'hijau':  'Hijau',
    'biru':   'Biru',
    'kuning': 'Kuning',
    'merah':  'Merah',
    'ungu':   'Ungu',
    'abu':    'Abu-abu',
}

# Pilihan ikon folder (tanpa emoji rumit supaya tetap rapi di HP).
FOLDER_IKON = {
    'folder':    'Folder',
    'buku':      'Buku',
    'dokumen':   'Dokumen',
    'bintang':   'Bintang',
    'arsip':     'Arsip',
}


def jatah_folder(p: str, ekstra: int = 0) -> int | None:
    """Jatah folder untuk paket `p` DITAMBAH `ekstra` dari AddOn.

    `ekstra` = User.folder_ekstra (dibeli lewat AddOn storage+folder).
    None = tak terbatas (paket penerbit — AddOn tidak menambah apa pun).
    """
    dasar = FOLDER_PAKET.get(p, 3)
    if dasar is None:
        return None                 # penerbit: tak terbatas, abaikan ekstra
    return dasar + max(0, int(ekstra or 0))


def paket_valid(p: str) -> bool:
    """True kalau nama paket dikenal."""
    return p in KUOTA_PAKET


def kuota_revisi_paket(p: str) -> int:
    """Jatah revisi AI per bulan untuk paket p (0 kalau paket tak dikenal)."""
    return KUOTA_PAKET.get(p, {}).get('revisi', 0)


def boleh_beli_addon(paket: str) -> bool:
    """AddOn terkunci untuk paket gratis (MASTER_PLAN §4.10)."""
    return paket not in PAKET_TANPA_ADDON and paket_valid(paket)


# ── PENGANTAR WA (GOWA) — dipatenkan Bos 27Sep26 ────────────────────────
# Pengirim: device 'eduai-wa-8514' (nomor 6285178138516), TERBUKTI kirim.
# DILARANG memakai UPB_WA_BLAST (3001) / slot OJS / nomor pribadi Bos.
EDUAI_GOWA_URL = os.getenv('EDUAI_GOWA_URL', 'http://172.17.0.1:3000')
EDUAI_GOWA_AUTH = os.getenv('EDUAI_GOWA_AUTH', 'gowa:sayangku@1')
EDUAI_GOWA_DEVICE = os.getenv('EDUAI_GOWA_DEVICE', 'eduai-wa-8514')
# PUTUSAN BOS 17 Okt 2026 (TERKUNCI): 8516 = admin EduAi · 8514 = admin Tridarma.
# Nomor TUJUAN admin EduAi = 0851-7813-8516 (6285178138516).
# ⚠️ Nomor ini JUGA nomor sesi device pengirim `eduai-wa-8514` (dan device
#    `OJS%252520Tridarma.id`) — jadi EduAi mengirim ke nomornya sendiri.
#    Itu DISENGAJA: kotak masuk admin ada di HP Bos yang memegang nomor 8516.
# Memakai: alarm fallback AI (wa.py:alarm_admin) + kartu 2 (nomor_wa_admin).
# JANGAN pakai 6285720505555 (nomor pribadi lama Bos — sudah tidak dipakai).
EDUAI_WA_ADMIN = os.getenv('EDUAI_WA_ADMIN', '6285178138516')
