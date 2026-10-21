"""Model database EduAi Publishing (SQLAlchemy 2.0).

Struktur:
  users        -> akun client (email, password hash, kuota, role)
  files        -> berkas milik client (nama, ukuran, path)
  transaksi    -> riwayat top-up QRIS
  sesi_edit    -> dokumen yang SEDANG dibuka di editor OnlyOffice
                  (dipakai untuk membatasi N dokumen bersamaan per user)
"""
from datetime import datetime, timedelta, timezone
import logging

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint,
    create_engine, event
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
)

from .config import DATABASE_URL

log = logging.getLogger('eduai')


class Base(DeclarativeBase):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nama: Mapped[str] = mapped_column(String(150), default='')
    kuota_mb: Mapped[int] = mapped_column(Integer, default=30)          # batas total
    # 14Sep26 (MASTER_PLAN §4.10): paket user untuk hitung kuota AI.
    # gratis | penulis | peneliti | penerbit. Default 'gratis' → aman untuk
    # user lama yang belum punya kolom ini (mereka memang belum bayar AI).
    paket: Mapped[str] = mapped_column(String(20), default='gratis', index=True)
    role: Mapped[str] = mapped_column(String(20), default='client')     # client | admin
    # ── ADDON tambahan (ACC Bos 15Sep26) ────────────────────────────────
    # Dibeli lewat AddOn `storage` (Rp 25.000 = +50 MB & +10 folder).
    # ⚠ `kuota_mb` dipakai di banyak tempat (main.py, ai.py) — AddOn storage
    #   MENAMBAH kolom itu langsung, sehingga semua pemeriksaan kuota lama
    #   otomatis ikut naik tanpa diubah satu per satu.
    # `folder_ekstra` = tambahan jatah folder dari AddOn (ditambah ke jatah
    #   paket oleh `jatah_folder()` di config.py).
    # Tanpa kedaluwarsa (ACC Bos 15Sep26): beli sekali, aktif terus.
    folder_ekstra: Mapped[int] = mapped_column(Integer, default=0)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)
    login_terakhir: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # ── IDENTITAS COVER (ACC Bos 26Sep26) ───────────────────────────────
    # Dipakai untuk HALAMAN JUDUL, LEMBAR PERSETUJUAN, dan KOP naskah.
    # Disimpan di User sebagai DEFAULT AKUN: mahasiswa tidak perlu mengetik
    # ulang setiap membuat naskah baru (putusan Bos: "simpan di akun +
    # boleh ditimpa per naskah").
    # ⚠ HANYA nama+NIM+kampus yang WAJIB; sisanya boleh kosong dan diisi
    #   kapan saja. LOGO BOLEH DILEWATI — sistem tetap jalan (ACC Bos).
    nama_lengkap: Mapped[str] = mapped_column(String(200), default='')
    nim: Mapped[str] = mapped_column(String(50), default='')
    nama_kampus: Mapped[str] = mapped_column(String(250), default='')
    kota_kampus: Mapped[str] = mapped_column(String(120), default='')
    fakultas: Mapped[str] = mapped_column(String(200), default='')
    program_studi: Mapped[str] = mapped_column(String(200), default='')
    # Logo kampus = BERKAS (tabel files), bukan blob di DB (berat).
    # 0 = belum ada / dilewati. Sistem tetap jalan tanpa logo.
    berkas_logo_id: Mapped[int] = mapped_column(Integer, default=0)
    # Pembimbing (putusan ⑨: diisi NANTI, opsional) — kolom disiapkan
    # sekarang supaya tidak perlu migrasi dua kali.
    pembimbing_1: Mapped[str] = mapped_column(String(200), default='')
    pembimbing_2: Mapped[str] = mapped_column(String(200), default='')

    files: Mapped[list['FileBerkas']] = relationship(
        back_populates='pemilik', cascade='all, delete-orphan')
    # Folder workspace milik user (ACC Bos 15Sep26).
    folders: Mapped[list['Folder']] = relationship(
        back_populates='pemilik', cascade='all, delete-orphan')

    @property
    def terpakai_bytes(self) -> int:
        """Byte yang dipakai = berkas + VERSI TERSIMPAN (ACC Bos 15Sep26).

        Backup/riwayat IKUT MENGHABISKAN KUOTA STORAGE — supaya user yang
        sering revisi terdorong menambah storage (model bisnis Bos).
        ⚠ Versi lama bernilai ukuran=0 → gratis, user lama tidak kaget.
        """
        total = sum(f.ukuran for f in self.files)
        for f in self.files:
            for v in (f.versi or []):
                total += (v.ukuran or 0)
        return total

    @property
    def terpakai_berkas_bytes(self) -> int:
        """Hanya berkas induk (tanpa versi) — dipakai untuk pesan terpisah."""
        return sum(f.ukuran for f in self.files)

    @property
    def terpakai_versi_bytes(self) -> int:
        """Hanya versi tersimpan — dipakai untuk pesan terpisah."""
        total = 0
        for f in self.files:
            for v in (f.versi or []):
                total += (v.ukuran or 0)
        return total

    @property
    def terpakai_mb(self) -> float:
        return self.terpakai_bytes / (1024 * 1024)

    @property
    def sisa_mb(self) -> float:
        return self.kuota_mb - self.terpakai_mb


class Folder(Base):
    """Folder workspace user (ACC Bos 15Sep26).

    Tujuan BISNIS: makin rapi workspace → user makin betah mengunggah →
    storage terpakai naik → dorongan upgrade. Folder juga jadi alasan
    upgrade tersendiri (jatah folder dibatasi per paket).

    ⚠ SATU TINGKAT saja (tidak bersarang) — user HP mudah bingung.
    ⚠ Menghapus folder TIDAK menghapus dokumen; dokumen jadi "tanpa folder".
    """
    __tablename__ = 'folders'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'), index=True, nullable=False)
    nama: Mapped[str] = mapped_column(String(100), nullable=False)
    # Warna & ikon supaya user "sayang" workspace-nya (ACC Bos 15Sep26).
    warna: Mapped[str] = mapped_column(String(20), default='hijau')
    ikon: Mapped[str] = mapped_column(String(20), default='folder')
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)

    pemilik: Mapped[User] = relationship(back_populates='folders')
    berkas: Mapped[list['FileBerkas']] = relationship(back_populates='folder')

    @property
    def jumlah_berkas(self) -> int:
        return len([f for f in (self.berkas or []) if not f.di_sampah])

    @property
    def ukuran_bytes(self) -> int:
        """Ukuran folder = berkas AKTIF + versi (konsisten dengan kuota)."""
        total = 0
        for f in (self.berkas or []):
            if f.di_sampah:
                continue
            total += (f.ukuran or 0)
            for v in (f.versi or []):
                total += (v.ukuran or 0)
        return total


class FileBerkas(Base):
    __tablename__ = 'files'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    nama: Mapped[str] = mapped_column(String(255), nullable=False)      # nama tampil
    nama_simpan: Mapped[str] = mapped_column(String(255), nullable=False)  # nama di disk
    ukuran: Mapped[int] = mapped_column(Integer, nullable=False)        # byte
    tipe: Mapped[str] = mapped_column(String(100), default='')
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)
    diubah: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)
    # Kapan USER terakhir menyimpan sendiri lewat editor (callback OnlyOffice).
    # ⚠ Dipisah dari `diubah` karena `diubah` JUGA berubah saat AI merevisi
    #   (simpan_versi menulis berkas). Kalau dicampur, UI tidak bisa membedakan
    #   "user mengedit" dari "AI baru merevisi" → peringatan riwayat keliru.
    # ACC Bos 14Sep26: dipakai untuk peringatan sebelum mengembalikan riwayat.
    disunting_pada: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # ── TONG SAMPAH (ACC Bos 14Sep26) ───────────────────────────────────
    # Berkas yang dihapus user TIDAK langsung hilang — pindah ke Tong Sampah
    # selama SAMPAH_HARI (30) hari, lalu dihapus permanen otomatis.
    # `terhapus_pada` NULL = berkas aktif (tidak di sampah).
    terhapus_pada: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, index=True)

    # ── FOLDER (ACC Bos 15Sep26) ────────────────────────────────────────
    # NULL = dokumen tanpa folder (di luar folder mana pun).
    # ⚠ Menghapus folder → dokumen TIDAK ikut terhapus (dipindah ke NULL).
    folder_id: Mapped[int | None] = mapped_column(
        ForeignKey('folders.id'), nullable=True, index=True)
    folder: Mapped['Folder | None'] = relationship(back_populates='berkas')

    pemilik: Mapped[User] = relationship(back_populates='files')
    # Versi/backup milik berkas ini — IKUT dihitung ke kuota storage
    # (ACC Bos 15Sep26). Dihapus otomatis saat berkasnya dihapus.
    versi: Mapped[list['VersiDokumen']] = relationship(
        cascade='all, delete-orphan', lazy='selectin')

    @property
    def di_sampah(self) -> bool:
        return self.terhapus_pada is not None

    @property
    def sisa_hari(self) -> int:
        """Sisa hari sebelum dihapus permanen (0 kalau bukan di sampah).

        ⚠ PELAJARAN 14Sep26: SQLite mengembalikan datetime NAIVE, sedangkan
        `_now()` bisa AWARE (kalau kolomnya pakai timezone=True). Kurangi
        langsung → "can't subtract offset-naive and offset-aware datetimes".
        Jadi NAIVE-kan dulu sebelum mengurangi.
        """
        if not self.terhapus_pada:
            return 0
        from .config import SAMPAH_HARI
        kini, mulai = _now(), self.terhapus_pada
        if kini.tzinfo is not None:
            kini = kini.replace(tzinfo=None)
        if mulai.tzinfo is not None:
            mulai = mulai.replace(tzinfo=None)
        return max(0, SAMPAH_HARI - (kini - mulai).days)

    @property
    def bisa_edit(self) -> bool:
        """True kalau OnlyOffice bisa membuka berkas ini."""
        from pathlib import Path as _P
        from .onlyoffice import EKSTENSI_EDIT, EKSTENSI_LIHAT
        ext = _P(self.nama).suffix.lower()
        return ext in EKSTENSI_EDIT or ext in EKSTENSI_LIHAT


class VersiDokumen(Base):
    """Versi hasil revisi AI per BAB — untuk rollback (ACC Bos 14Sep26).

    PRINSIP: hasil revisi AI TIDAK PERNAH menimpa dokumen asli. Yang terjadi:
      - setiap revisi menghasilkan VERSI BARU (baris baru di tabel ini)
      - versi yang dipakai mahasiswa = versi dengan `terpakai=True`
      - tersimpan maksimal VERSI_SIMPAN (2) versi lama per (file, bab)
      - versi ke-3 muncul → versi TERTUA auto-dibuang (seperti gear berputar)
    """

    __tablename__ = 'versi_dokumen'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    file_id: Mapped[int] = mapped_column(ForeignKey('files.id'), index=True, nullable=False)
    # Bab yang direvisi: 'BAB I', 'BAB II', ... atau '__seluruh__' kalau tak ada bab
    bab: Mapped[str] = mapped_column(String(80), default='__seluruh__', index=True)
    # Nomor urut versi (1, 2, 3, ...) per (file, bab)
    nomor: Mapped[int] = mapped_column(Integer, default=1)
    # Isi teks bab hasil revisi
    isi: Mapped[str] = mapped_column(Text, nullable=False)
    # Ringkasan komentar yang dikerjakan (untuk ditampilkan di UI)
    komentar: Mapped[str] = mapped_column(Text, default='')
    model: Mapped[str] = mapped_column(String(80), default='')
    # Ukuran versi dalam byte — DIHITUNG KE KUOTA STORAGE (ACC Bos 15Sep26).
    # ⚠ Versi lama (sebelum kolom ini ada) bernilai 0 = GRATIS, supaya user
    #   lama tidak mendadak kena batas kuota.
    ukuran: Mapped[int] = mapped_column(Integer, default=0)
    # Sumber titik mundur: 'ai' (revisi AI) atau 'user' (simpan manual).
    # ACC Bos 14Sep26: auto save TIDAK membuat titik mundur — hanya dua ini.
    # Dipakai UI untuk menulis "✨ AI" atau "Anda" di riwayat.
    sumber: Mapped[str] = mapped_column(String(10), default='ai')
    # True = versi ini yang sedang dipakai. Maksimal 1 True per (file, bab).
    terpakai: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    # ══ C10 (25Sep26) — ARSIP, BUKAN HAPUS ══════════════════════════════
    #  🚨 BUG NYATA (temuan uji C7): "gear" dulu memakai `db.delete()` →
    #  versi lama yang BERISI hilang PERMANEN. Bukti: v57 (4.522 kar) LENYAP
    #  setelah 2 putaran revisi kosong → tidak ada lagi yang bisa dipulihkan.
    #  Sekarang versi tua hanya DITANDAI arsip: hilang dari daftar aktif &
    #  tombol mundur, TAPI datanya tetap ada di DB untuk pemulihan.
    #  DEFAULT 0 (False) supaya versi LAMA tetap berarti "aktif".
    diarsipkan: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)

    __table_args__ = (
        UniqueConstraint('file_id', 'bab', 'nomor', name='uq_versi_file_bab_nomor'),
    )

    @property
    def label(self) -> str:
        """Label siap tampil: '14 Sep, 10:32'."""
        try:
            return self.dibuat.strftime('%d %b, %H:%M')
        except Exception:                                 # pragma: no cover
            return '-'

    @property
    def kapan(self) -> str:
        """Waktu dalam bahasa manusia — ACC Bos 14Sep26.

        Riwayat ditampilkan TANPA nomor versi, pakai bahasa waktu saja:
        '2 menit lalu', '5 jam lalu', '14 Sep'.
        ⚠ SQLite mengembalikan datetime NAIVE → samakan dulu sebelum kurangi.
        """
        try:
            kini = _now()
            mulai = self.dibuat
            if kini.tzinfo is not None:
                kini = kini.replace(tzinfo=None)
            if mulai.tzinfo is not None:
                mulai = mulai.replace(tzinfo=None)
            detik = max(0, (kini - mulai).total_seconds())
            if detik < 60:
                return 'baru saja'
            if detik < 3600:
                return '%d menit lalu' % (detik // 60)
            if detik < 86400:
                return '%d jam lalu' % (detik // 3600)
            if detik < 172800:
                return 'kemarin'
            if detik < 604800:
                return '%d hari lalu' % (detik // 86400)
            return mulai.strftime('%d %b')
        except Exception:                                 # pragma: no cover
            return '-'

    @property
    def dari_ai(self) -> bool:
        return (self.sumber or 'ai') != 'user'

    @property
    def sumber_nama(self) -> str:
        """Nama sumber untuk UI: '✨ AI' atau 'Anda'."""
        return '✨ AI' if self.dari_ai else 'Anda'


class VersiPipa(Base):
    """Pendamping SEBUAH baris `versi_dokumen`: hasil revisi dalam bentuk
    mentah KUTIP-ASLI/GANTI-JADI (Opsi D, 29Sep26 — putusan Bos "D1 + (a)").

    ═══ KENAPA ADA ═══
    Akar terukur 29Sep26: `bersihkan_jawaban_ai()` MEMBUANG kerangka
    KUTIP/GANTI saat menyimpan, sehingga `versi_dokumen.isi` berisi teks
    polos. Pintu "Tulis hasil ke dokumen" (`/api/ai/v1/terapkan`)
    memeriksa teks itu dengan `pipa.periksa()` → selalu `editan=0` →
    jatuh ke jalur mundur (Opsi A kini menolaknya dengan 422).
    Cakupan terukur: 8/8 versi AI terakhir = editan=0.

    Dengan pendamping ini, `terapkan` membaca bentuk mentah → menemukan
    editan → menulis PRESISI (paragraf yang dikutip saja), tanpa perlu
    salin-tempel manual.

    ATURAN SIMPAN:
      · SATU baris per baris versi (`versi_id` unik) — mundur ke versi
        lain otomatis memakai pendamping versi itu (atau 422 jujur).
      · Tabel BARU — `versi_dokumen` TIDAK disentuh (aturan: jangan ubah
        tabel lama). Dibuat `create_all()` di `init_db()`.
      · Kalau pendamping gagal disimpan, revisi TETAP sukses; pintu
        terapkan akan jujur menolak (jalur Salin hasil) — bukan rusak.
    """

    __tablename__ = 'versi_pipa'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    versi_id: Mapped[int] = mapped_column(
        ForeignKey('versi_dokumen.id'), unique=True, index=True,
        nullable=False)
    file_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    # Bentuk mentah siap pakai pipa.periksa() — penomoran K sudah diurutkan
    # ulang supaya nomor kembar antar-bagian tidak saling membatalkan.
    teks: Mapped[str] = mapped_column(Text, nullable=False)
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Transaksi(Base):
    __tablename__ = 'transaksi'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    order_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    paket: Mapped[str] = mapped_column(String(50), nullable=False)
    tambahan_mb: Mapped[int] = mapped_column(Integer, nullable=False)
    jumlah: Mapped[int] = mapped_column(Integer, nullable=False)        # rupiah
    # 12Sep26: status ke-5 = 'expired' (user tidak bayar dalam batas waktu).
    # Beda makna dengan 'gagal' (ditolak/mati di sisi Pakasir).
    status: Mapped[str] = mapped_column(String(30), default='pending')
    bukti: Mapped[str | None] = mapped_column(Text, nullable=True)
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)
    dibayar: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # 12Sep26: batas berlaku QR (dari Pakasir `expired_at`). Dipakai auto-expire
    # LAZY — tanpa cron. Kalau NULL, fallback ke `dibuat + QRIS_EXPIRE_MENIT`.
    kedaluwarsa: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SesiEdit(Base):
    """Satu baris = satu dokumen yang SEDANG dibuka di editor OnlyOffice.

    KENAPA perlu: setiap dokumen yang dibuka OnlyOffice menahan 1 proses
    editor + cache .bin + 1 koneksi WebSocket. Tanpa pembatasan, seorang
    user bisa membuka 5 dokumen sekaligus dan menghabiskan CPU/RAM VPS.

    Cara pakai:
      - Buka  : baris dibuat (atau diperbarui kalau file SAMA sudah terbuka)
      - Pakai : editor kirim heartbeat tiap 60 dtk -> perbarui terakhir_aktif
      - Tutup : baris dihapus (didahului forcesave supaya edit tidak hilang)
      - Basi  : terakhir_aktif lebih tua dari SESI_IDLE_MENIT -> auto-dihapus
    """
    __tablename__ = 'sesi_edit'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    file_id: Mapped[int] = mapped_column(ForeignKey('files.id'), index=True, nullable=False)
    # Kunci dokumen versi saat dibuka (sama dengan 'key' yang dikirim ke OnlyOffice).
    # Dipakai untuk forcesave agar OnlyOffice menyimpan dokumen yang BENAR.
    kunci_oo: Mapped[str] = mapped_column(String(120), default='')
    # ⚠ timezone=True WAJIB: tanpa ini SQLite mengembalikan datetime NAIVE,
    # lalu `_now() - terakhir_aktif` melempar
    # "can't subtract offset-naive and offset-aware datetimes" (bug 12Sep26).
    dibuka: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    terakhir_aktif: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, index=True)

    berkas: Mapped[FileBerkas] = relationship()


# ══════════════════════════════════════════════════════════════════════════
# SISTEM KUOTA & CREDIT AI — MASTER_PLAN §4.10 (ACC Bos 13Sep26)
#
# MASALAH yang dipecahkan:
#   Sebelum ini gerbang AI BINER: `_member_berbayar()` = "punya ≥1 transaksi
#   sukses". Jadi beli Rp 50rb = AI UNLIMITED, tidak ada hitungan apa pun.
#
# STRATEGI BISNIS (jangan diubah tanpa ACC Bos):
#   • PAKET  = tiket masuk (margin tebal, dibeli sekali)
#   • ADDON  = mesin uang (murah, dibeli berulang)
#   • Kuota habis → TAWARKAN ADDON, JANGAN dorong upgrade paket
#   • Sisa credit HANGUS tiap tanggal 1 (reset bulanan, lazy tanpa cron)
# ══════════════════════════════════════════════════════════════════════════


class PemakaianAI(Base):
    """Satu baris per (user, bulan). Menghitung pemakaian AI bulan berjalan.

    KENAPA per-bulan bukan counter di users: supaya reset bulanan cukup
    dengan melihat `bulan` — data bulan lama tetap tersimpan sebagai riwayat
    (berguna untuk analitik & audit).
    """
    __tablename__ = 'pemakaian_ai'
    __table_args__ = (UniqueConstraint('user_id', 'bulan', name='uq_pemakaian_user_bulan'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    bulan: Mapped[str] = mapped_column(String(7), index=True, nullable=False)  # 'YYYY-MM'
    jumlah_revisi: Mapped[int] = mapped_column(Integer, default=0)      # sudah dipakai
    jumlah_simulasi: Mapped[int] = mapped_column(Integer, default=0)    # Mode Belajar L3
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)
    diubah: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class PembelianAddon(Base):
    """AddOn yang dibeli user. `sisa_kuota` dipotong saat dipakai.

    PENTING: AddOn TERKUNCI untuk paket `gratis` (validasi di BACKEND,
    bukan hanya UI) — sesuai MASTER_PLAN §4.10.
    """
    __tablename__ = 'pembelian_addon'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    jenis: Mapped[str] = mapped_column(String(40), index=True, nullable=False)  # ai | konversi | publish | belajar
    sisa_kuota: Mapped[int] = mapped_column(Integer, default=0)
    harga: Mapped[int] = mapped_column(Integer, default=0)              # rupiah saat beli
    order_id: Mapped[str] = mapped_column(String(100), default='', index=True)
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)
    # AddOn dengan masa berlaku (mis. Belajar per naskah). NULL = tidak kedaluwarsa.
    kedaluwarsa: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class BelajarNaskah(Base):
    """Satu baris per aktivasi Mode Belajar pada satu naskah.

    HEMAT TOKEN (MASTER_PLAN §4.8): insight & soal dihitung SEKALI lalu
    disimpan permanen di sini (kolom JSON) — TIDAK dihitung ulang tiap buka.
    Jaminan ke user: "Mode Belajar milikmu tersimpan permanen — tidak hangus".

    MASTER_PLAN §4.10 menyebut tabel ini `belajar_naskah`.
    """
    __tablename__ = 'belajar_naskah'
    __table_args__ = (UniqueConstraint('file_id', name='uq_belajar_file'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey('files.id'), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default='aktif')    # aktif | selesai
    # Insight & soal tersimpan sebagai JSON (di luar skema relasional —
    # isinya tumbuh per bab: mini insight BAB I/II → penuh saat BAB III).
    insight_json: Mapped[str] = mapped_column(Text, default='{}')
    soal_json: Mapped[str] = mapped_column(Text, default='{}')
    bab_selesai: Mapped[str] = mapped_column(Text, default='[]')        # JSON list
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)
    diubah: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class KonversiNaskah(Base):
    """Satu baris per KONVERSI naskah → artikel jurnal (07 Okt 2026).

    ⭐ SALINAN POLA dari `BelajarNaskah` (models.py:472) — SENGAJA sama supaya
    tidak ada sistem baru. Bedanya cuma NAMA TABEL & BENTUK CATATAN hasil.

    KENAPA tabel ini WAJIB ADA (bukan boleh):
    Tanpa tabel ini, pemakaian konversi TIDAK TERLACAK → user bisa konversi
    berkali-kali tanpa terpotong = KEBOCORAN UANG (risiko R2, laporan 07Okt26).

    ATURAN (putusan Bos 07Okt26):
      · melekat pada 1 naskah, SEKALI JADI (revisi kena token, bukan konversi ulang)
      · kuota terpakai SAAT PROSES (bukan saat preview dibuka — lihat SOT §C.8)
      · naskah WAJIB milik user sendiri
      · status: 'proses' (sedang jalan) → 'beres' | 'gagal'
        'gagal' = AI gagal TEKNIS → token dikembalikan (kembalikan_banyak)

    CATATAN: `file_id` TIDAK unik (beda dari belajar) — karena naskah yang sama
    BOLEH dikonversi lagi setelah dihapus & bayar ulang (putusan Bos: "konversi
    lagi tetap bayar lagi"). Yang mencegah giling-gratis adalah POTONG KUOTA,
    bukan unique constraint.
    """
    __tablename__ = 'konversi_naskah'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey('files.id'), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default='proses')   # proses | beres | gagal
    #  Dari mana kuota diambil: 'paket' | 'addon' — untuk audit & tampilan.
    sumber_kuota: Mapped[str] = mapped_column(String(20), default='paket')
    #  Jenis naskah hasil deteksi: kuantitatif | kualitatif | review (bisa ditimpa user).
    jenis: Mapped[str] = mapped_column(String(30), default='')
    #  Hasil konversi disimpan sebagai JSON (di luar skema relasional, seperti belajar).
    #  Isi: {'artikel': {...}, 'peta_bab': [...], 'periksa': {...}, 'jenis': '...'}
    hasil_json: Mapped[str] = mapped_column(Text, default='{}')
    #  Cacat/kesalahan teknis (kalau status='gagal') — jujur ke user.
    galat: Mapped[str] = mapped_column(Text, default='')
    #  Token/AddOn yang DIPOTONG — supaya bisa dikembalikan utuh saat gagal teknis.
    token_dipotong: Mapped[int] = mapped_column(Integer, default=0)
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)
    diubah: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class ProfilDokumen(Base):
    """Ingatan dokumen — hasil AI baca SELURUH naskah 1x teliti (MASTER_PLAN §4.11).

    === SALINAN POLA DARI PENELITIAN-BOT (SUMBER READ-ONLY) ===
    Asal: /opt/data/services/penelitian-bot/prisma/schema.prisma
          model Project baris 40-45 -> `briefStatus` + `brief Json?`
          model AgentState baris 120-131 -> akumulasi data per agen
    ADAPTASI: di EduAi, `brief` (Research Brief) menempel ke BERKAS user
    (file_id), bukan ke "Project" — karena user EduAi mengunggah naskah jadi.

    KENAPA ada tabel ini: supaya AI tidak membaca ulang dokumen tiap revisi
    (mahal + lambat). Sekali baca teliti -> simpan -> pakai ulang.
    Kalau naskah berubah (sidik_jari beda) -> baca ulang bab yang berubah SAJA
    (GRATIS, tanggung sistem — ACC Bos 15Sep26).
    """
    __tablename__ = 'profil_dokumen'
    __table_args__ = (UniqueConstraint('file_id', name='uq_profil_file'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey('files.id'), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)

    sumber: Mapped[str] = mapped_column(String(20), default='unggah')      # unggah | buat_baru
    # 4 kategori (MASTER_PLAN §4.11): akademik_1bab | akademik_proposal |
    # akademik_lengkap | dokumen_umum
    kategori: Mapped[str] = mapped_column(String(30), default='')
    judul: Mapped[str] = mapped_column(String(500), default='')
    jenjang: Mapped[str] = mapped_column(String(10), default='')            # S1|S2|S3|umum
    bidang: Mapped[str] = mapped_column(String(120), default='')
    mode_penelitian: Mapped[str] = mapped_column(String(30), default='')    # kuantitatif|kualitatif|slr|non_ilmiah

    # ── TIMPA IDENTITAS COVER per NASKAH (ACC Bos 26Sep26) ──────────────
    # Kosong = pakai nilai dari User (akun). Terisi = menang (mis. naskah
    # kedua mahasiswa yang sama tapi kampus/kota berbeda).
    nama_lengkap: Mapped[str] = mapped_column(String(200), default='')
    nim: Mapped[str] = mapped_column(String(50), default='')
    nama_kampus: Mapped[str] = mapped_column(String(250), default='')
    kota_kampus: Mapped[str] = mapped_column(String(120), default='')
    fakultas: Mapped[str] = mapped_column(String(200), default='')
    program_studi: Mapped[str] = mapped_column(String(200), default='')
    berkas_logo_id: Mapped[int] = mapped_column(Integer, default=0)
    pembimbing_1: Mapped[str] = mapped_column(String(200), default='')
    pembimbing_2: Mapped[str] = mapped_column(String(200), default='')

    # ── ASAL NASKAH (ACC Bos 26Sep26) — 2 label saja ────────────────────
    # 'eduai' = ditulis EduAi dari nol · 'user' = naskah bawaan user
    # Dipakai AI supaya TIDAK menilai naskah user dengan standar EduAi
    # (pagar ⑰: metode user DILARANG diubah, hanya diingatkan).
    asal_naskah: Mapped[str] = mapped_column(String(10), default='user')

    # ── PETA HALUS (ACC Bos 26Sep26) ────────────────────────────────────
    # Daftar rekomendasi per bab+subbab hasil baca pertama (JSON).
    # peta_sidik = hash naskah saat peta dibuat → kalau naskah berubah,
    # peta lama tidak dipakai ulang (pagar kredibilitas).
    peta_json: Mapped[str] = mapped_column(Text, default='')
    peta_sidik: Mapped[str] = mapped_column(String(64), default='')
    peta_dibuat: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # ALUR ARGUMENTASI (MASTER_PLAN §4.14) — diputuskan AI, BUKAN ditanya user
    alur: Mapped[str] = mapped_column(String(30), default='')               # kuantitatif_deduktif|kualitatif_induktif|kualitatif_deduktif

    # Research Brief = "kebenaran tunggal" (app/brief.py) — JSON, lihat BRIEF_TEMPLATE
    brief_json: Mapped[str] = mapped_column(Text, default='{}')
    # Kitab Istilah — MASTER_PLAN §4.12 (kunci istilah agar tidak gonta-ganti)
    istilah_json: Mapped[str] = mapped_column(Text, default='[]')
    # Struktur bab: [{"nomor":"BAB I","judul":"PENDAHULUAN","karakter":43000}]
    struktur_json: Mapped[str] = mapped_column(Text, default='[]')

    # STANDAR PENULISAN (26Sep26): panduan penulisan kampus yang diunggah
    # user per naskah (JSON hasil ekstraksi tanpa AI — app/standar_penulisan.py).
    # '' = belum ada → AI pakai ATURAN_BAKU (pedoman bawaan EduAi).
    panduan_json: Mapped[str] = mapped_column(Text, default='')

    # ── JURNAL / REFERENSI (ACC Bos 06Okt26, Opsi A) ──────────────────────
    # Daftar artikel jurnal per naskah + penanda BAB (JSON). Meniru pola
    # `peta_json` + `peta_sidik` yang SUDAH TERBUKTI — bukan sistem baru.
    #   jurnal_json  = {"<bab>": [ {artikel...}, ... ], "_manual": {...}}
    #                  tiap artikel bentuknya SAMA dengan app/pustaka.py
    #                  (title/authors/year/journal/doi/garuda_id/doi_status)
    #   jurnal_sidik = hash (judul+kata kunci) saat daftar dibuat → kalau
    #                  judul/kk berubah, hasil lama tidak dipakai ulang.
    # '' = belum ada pencarian tersimpan.
    jurnal_json: Mapped[str] = mapped_column(Text, default='')
    jurnal_sidik: Mapped[str] = mapped_column(String(64), default='')

    # Sidik jari isi (SHA-256) — pembanding cepat apakah naskah berubah.
    # BEDA naskah -> ingatan basi -> baca ulang bab berubah (GRATIS).
    sidik_jari: Mapped[str] = mapped_column(String(64), default='', index=True)

    status: Mapped[str] = mapped_column(String(20), default='menganalisis')  # menganalisis|siap|butuh_tinjauan
    dibaca_pada: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)
    diubah: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class SectionState(Base):
    """Ingatan PER SUB-BAB naskah (MASTER_PLAN §4.11/§4.15 komponen 3).

    === SALINAN POLA DARI PENELITIAN-BOT (SUMBER READ-ONLY) ===
    Asal: /opt/data/services/penelitian-bot/prisma/schema.prisma
          model SectionState baris 135-152:
            projectId + sectionId (unique) | sectionTitle | category |
            version | content | wordCount | lastIntent | updatedAt
    ADAPTASI: `projectId` -> `file_id` (EduAi = berkas, bukan project).
              `wordCount` -> `char_count` (EduAi menghitung KARAKTER).

    KENAPA ada: (a) AI ingat apa yang sudah ditulis per sub-bab -> tidak
    tumpang tindih; (b) deteksi bab = PENENTU HARGA Token Revisi (§4.13);
    (c) tahu apakah revisi terakhir dari AI atau dari user.
    """
    __tablename__ = 'section_state'
    __table_args__ = (
        UniqueConstraint('file_id', 'section_id', name='uq_section_file'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey('files.id'), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)

    section_id: Mapped[str] = mapped_column(String(30), nullable=False)      # '1.1'|'4.2'|'BAB I'|'pasal_1'
    section_title: Mapped[str] = mapped_column(String(255), default='')
    kategori: Mapped[str] = mapped_column(String(20), default='bab')         # bab|meta|lampiran|pasal

    versi: Mapped[int] = mapped_column(Integer, default=1)
    isi_teks: Mapped[str] = mapped_column(Text, default='')
    char_count: Mapped[int] = mapped_column(Integer, default=0)

    # Sidik jari PER-BAB — deteksi bab mana yang berubah (MASTER_PLAN §4.12).
    # Bab berubah -> ingatan basi -> baca ulang bab itu (GRATIS, tanggung sistem).
    sidik_bab: Mapped[str] = mapped_column(String(64), default='', index=True)

    # Jenis revisi terakhir -> menentukan PENGALI Token Revisi (§4.13/§4.15 #5)
    jenis_revisi: Mapped[str] = mapped_column(String(30), default='')        # TAMBAH_DATA|PERKAYA_NARASI|REVISI|GANTI_METODE|HAPUS|PERTANYAAN
    konteks_jenis: Mapped[str] = mapped_column(String(30), default='')       # paragraf|sub_bab|bab|dokumen

    # Siapa yang terakhir mengubah: 'ai' | 'user'.
    # ⚠ PENTING: kolom `diubah` di FileBerkas dipakai AI DAN user, jadi TIDAK
    # bisa dipakai mendeteksi editan user. Kolom INI yang membedakan.
    sumber_terakhir: Mapped[str] = mapped_column(String(10), default='')
    diubah_pada: Mapped[datetime] = mapped_column(DateTime, default=_now)

    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)
    diubah: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class RevisiHistory(Base):
    """Riwayat revisi per sub-bab — titik mundur + catatan biaya.

    === SALINAN POLA DARI PENELITIAN-BOT (SUMBER READ-ONLY) ===
    Asal: /opt/data/services/penelitian-bot/prisma/schema.prisma
          model RevisiHistory baris 154-167:
            projectId | sectionId | version | intent | userRequest |
            oldContent | newContent | diffSummary | createdAt

    ADAPTASI: + kolom BIAYA (token_in/token_out/token_revisi) supaya tarif
    Token Revisi (§4.13) bisa diaudit dari riwayat nyata, bukan tebakan.
    `oldContent`/`newContent` TIDAK disimpan penuh di sini (boros) — isi lama
    ada di `versi_dokumen`; di sini cukup ringkasan perubahan.
    """
    __tablename__ = 'revisi_history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey('files.id'), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)

    section_id: Mapped[str] = mapped_column(String(30), default='')
    versi: Mapped[int] = mapped_column(Integer, default=1)
    intent: Mapped[str] = mapped_column(String(30), default='')              # lihat SectionState.jenis_revisi
    komentar_dosen: Mapped[str] = mapped_column(Text, default='')
    ringkasan_perubahan: Mapped[str] = mapped_column(Text, default='')
    diff_summary: Mapped[str] = mapped_column(Text, default='')

    # ── BIAYA NYATA (audit tarif §4.13) ──
    token_in: Mapped[int] = mapped_column(Integer, default=0)
    token_out: Mapped[int] = mapped_column(Integer, default=0)
    token_revisi: Mapped[int] = mapped_column(Integer, default=0)            # hasil rumus (÷10.000, pengali, cap)
    pengali: Mapped[int] = mapped_column(Integer, default=1)                 # 1|3|4|5
    model_ai: Mapped[str] = mapped_column(String(120), default='')           # nama model LENGKAP apa adanya

    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ProsesAI(Base):
    """STATUS PROSES AI DI LATAR BELAKANG (Langkah A+B, ACC Bos 16Sep26).

    === KENAPA TABEL INI ADA (akar masalah, terukur 16Sep26) ===
    Revisi naskah besar berjalan SINKRON: HTTP request menunggu AI sampai
    selesai. Cloudflare memutus koneksi di ~125 detik (HTTP 524) → user lihat
    ERROR, padahal kuota SUDAH dipotong (9→7) dan hasil TIDAK tersimpan
    (revisi_history=0, versi_dokumen tak bertambah).

    SOLUSI (rancangan Bos sendiri, MASTER_PLAN §4.12 poin F "KEDUANYA"):
    request user hanya MENITIPKAN pekerjaan lalu langsung dibalas pendek
    ("sedang diproses") → Cloudflare tidak pernah memutus. Pekerjaan jalan di
    LATAR BELAKANG, hasilnya ditulis ke tabel ini, dan halaman memantau
    lewat /api/ai/v1/proses/{id} (tahap NYATA, bukan persen karangan).

    === ATURAN YANG DIPATUHI ===
    - Tabel BARU: tabel lama TIDAK diubah (aman untuk data produksi).
    - `tahap` = TAHAP NYATA (Membaca/Blueprint/Bab X/Periksa), BUKAN persen.
    - Hasil disimpan di sini, jadi bagian SEDANG DIPERIKSA, dan `galat` untuk
      pesan gagal — supaya kuota bisa dikembalikan dengan bukti, bukan tebakan.
    """
    __tablename__ = 'proses_ai'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # ⚠️ token acak (bukan id berurutan) supaya user lain tidak bisa mengintip
    #    proses orang lain hanya dengan menebak angka.
    kode: Mapped[str] = mapped_column(String(32), unique=True, index=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True,
                                        nullable=False)
    file_id: Mapped[int] = mapped_column(ForeignKey('files.id'), index=True,
                                         nullable=True)

    # menunggu | jalan | selesai | gagal | dibatalkan
    status: Mapped[str] = mapped_column(String(12), default='menunggu',
                                        index=True)
    # teks tahap NYATA yang ditampilkan ke user (mis. "Menulis Bab II")
    tahap: Mapped[str] = mapped_column(String(120), default='')

    bagian_ke: Mapped[int] = mapped_column(Integer, default=0)       # sedang bagian ke-N
    jumlah_bagian: Mapped[int] = mapped_column(Integer, default=1)   # total bagian
    panjang: Mapped[int] = mapped_column(Integer, default=0)         # panjang naskah (karakter)

    # Hasil pekerjaan. Ditaruh di tabel INI dulu (bukan langsung ke .docx)
    # supaya user yang meninggalkan halaman tidak menemukan dokumen berubah
    # sendiri. Penulisan ke dokumen dilakukan saat user MEMBUKA hasilnya.
    hasil: Mapped[str] = mapped_column(Text, default='')
    # Ringkasan per bagian — siap dipakai untuk menulis .docx nanti.
    hasil_json: Mapped[str] = mapped_column(Text, default='')
    galat: Mapped[str] = mapped_column(Text, default='')

    # Perintah asli dititipkan di sini agar pekerjaan bisa dilanjutkan walau
    # proses HTTP-nya sudah berakhir.
    komentar_json: Mapped[str] = mapped_column(Text, default='')
    jenis_dokumen: Mapped[str] = mapped_column(String(30), default='')
    model_ai: Mapped[str] = mapped_column(String(120), default='')
    # Token nyata hasil kerja (dasar rumus Token Revisi ÷10.000)
    token_in: Mapped[int] = mapped_column(Integer, default=0)
    token_out: Mapped[int] = mapped_column(Integer, default=0)
    token_revisi: Mapped[int] = mapped_column(Integer, default=0)
    # Sudah dibaca user? (untuk lonceng notifikasi — acc Bos 16Sep26 poin 1)
    dibaca: Mapped[int] = mapped_column(Integer, default=0)

    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)
    diubah: Mapped[datetime] = mapped_column(DateTime, default=_now,
                                             onupdate=_now)
    selesai: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class Notifikasi(Base):
    """Kotak masuk notifikasi EduAi (ACC Bos 17Sep26).

    KENAPA tabel TERSENDIRI, bukan menumpang `proses_ai`:
    `proses_ai` hanya bisa menampung notifikasi yang LAHIR dari sebuah
    proses revisi. Padahal banyak kejadian penting yang tidak terkait proses
    — pembayaran masuk, kuota menipis, ruang penyimpanan hampir penuh.
    Menumpangkan semuanya ke `proses_ai` akan memaksa membuat baris proses
    palsu. Tabel ini juga menjadi fondasi NOTIFIKASI PEMBIMBING nanti
    (butuh penerima selain pemilik naskah).

    Teks DISIMPAN saat dibuat (bukan dihitung saat dibaca) — supaya kalimat
    yang sudah terkirim tidak berubah kalau gaya bahasa diperbarui nanti.
    """
    __tablename__ = 'notifikasi'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    #  Kunci anti-spam, mis. 'kuota_hampir_habis:2' atau 'revisi_selesai:47'.
    kunci: Mapped[str] = mapped_column(String(120), default='', index=True)
    jenis: Mapped[str] = mapped_column(String(40), default='')
    judul: Mapped[str] = mapped_column(String(160), default='')
    isi: Mapped[str] = mapped_column(Text, default='')
    tombol: Mapped[str] = mapped_column(String(40), nullable=True)
    #  kabar | ingat | bantu | semangat — dipakai UI memilih warna lembut.
    nada: Mapped[str] = mapped_column(String(20), default='bantu')
    file_id: Mapped[int] = mapped_column(Integer, nullable=True)
    dibaca: Mapped[int] = mapped_column(Integer, default=0, index=True)
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Setelan(Base):
    """Setelan aplikasi yang bisa diubah ADMIN dari halaman /pengaturan.

    ═══ KENAPA ADA ═══
    Sebelumnya TOKEN_REVISI_PER hanya bisa diubah lewat `.env` + deploy
    (butuh Wulan, butuh restart container). Bos minta bisa naik-turun
    mengikuti pasar tanpa deploy (permintaan 24Sep26).

    ═══ URUTAN PRIORITAS (WAJIB DIPATUHI) ═══
    DB (tabel ini)  >  .env  >  default di config.py
    DB menang supaya admin bisa ubah langsung dari browser. Kalau baris DB
    dihapus, nilai kembali ke .env/default.

    ═══ RIWAYAT ═══
    Setiap perubahan dicatat di `SetelanRiwayat` — supaya kalau harga
    berubah dan ada pertanyaan ("kok tadi murah sekarang mahal?"), jejaknya
    ada: siapa, kapan, dari berapa → berapa.
    """
    __tablename__ = 'setelan'

    kunci: Mapped[str] = mapped_column(String(60), primary_key=True)
    nilai: Mapped[str] = mapped_column(String(120), default='')
    diubah: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)
    oleh: Mapped[str] = mapped_column(String(160), default='')


class SetelanRiwayat(Base):
    """Jejak perubahan setelan (siapa, kapan, dari → ke)."""
    __tablename__ = 'setelan_riwayat'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kunci: Mapped[str] = mapped_column(String(60), index=True)
    nilai_lama: Mapped[str] = mapped_column(String(120), default='')
    nilai_baru: Mapped[str] = mapped_column(String(120), default='')
    oleh: Mapped[str] = mapped_column(String(160), default='')
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)


class PembatalanKuota(Base):
    """Jejak pembatalan kuota saat user ROLLBACK naskah (ACC Bos 17Sep26).

    ═══ MASALAH YANG DITUTUP ═══
    User revisi (kuota terpotong) → lalu rollback naskah. Kalau kuota selalu
    dikembalikan, user bisa MENGGILING GRATIS: minta revisi, salin hasilnya,
    rollback, ulangi. AI bekerja 10× sementara user membayar 0×.

    ═══ ATURAN (OPSI C — keputusan Bos 17Sep26) ═══
    Kuota dibalikkan HANYA bila SEMUA ini terpenuhi:
      1. hasil revisi BELUM pernah dibuka user (`proses_ai.dibaca = 0`);
      2. hasil BELUM diterapkan ke dokumen (versi belum `terpakai`);
      3. belum memakai hak ini untuk naskah ini HARI INI.
    Pagar: maksimal 1× per NASKAH (bukan per akun) · jeda 20 menit sejak
    revisi selesai · rollback harus ke versi SEBELUM revisi itu.

    Notifikasi WAJIB dikirim apa pun hasilnya (permintaan Bos).
    """
    __tablename__ = 'pembatalan_kuota'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    file_id: Mapped[int] = mapped_column(ForeignKey('files.id'), index=True)
    kode_proses: Mapped[str] = mapped_column(String(40), default='')
    #  Berapa Token Revisi yang benar-benar dibalikkan (0 = tidak dibalik).
    jumlah_kembali: Mapped[int] = mapped_column(Integer, default=0)
    #  Kenapa TIDAK dibalikkan — untuk teknisi, BUKAN untuk ditampilkan ke user.
    alasan: Mapped[str] = mapped_column(String(60), default='')
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)


# ══════════════════════════════════════════════════════════════════════════
# JATAH PENCARIAN JURNAL MANUAL (ACC Bos 06Okt26)
#
# PUTUSAN BOS: yang dihitung = Pencarian MANUAL saja (pencarian AI gratis
# sampai kerangka) · harga 1 Token Revisi per pencarian · GRATIS 2× per
# siklus 7 hari · siklus dihitung sejak AWAL PEMAKAIAN user (bukan daftar) ·
# batas per USER (bukan per naskah) · dihitung di SERVER, bukan browser.
#
# Meniru pola `pembatalan_kuota`: jejak per user + waktu + sebab.
# ⚠️ TABEL BARU saja — tidak ada tabel lama yang diubah.
# ══════════════════════════════════════════════════════════════════════════

JATAH_GRATIS = 2        # 2× percobaan gratis
SIKLUS_HARI = 7         # per 7 hari sejak awal pemakaian
HARGA_TOKEN = 1         # 1 token setelah jatah habis


class PencarianManual(Base):
    """Jejak tiap pencarian MANUAL user (untuk hitung jatah 2×/7hari).

    Semua pencarian manual dicatat (gratis maupun berbayar) supaya:
      · jatah bisa dihitung (berapa gratis yang sudah dipakai siklus ini);
      · `awal pemakaian` bisa diketahui (baris PERTAMA user);
      · ada jejak audit (siapa cari apa, kapan, di bab mana).
    """
    __tablename__ = 'pencarian_manual'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    file_id: Mapped[int | None] = mapped_column(ForeignKey('files.id'),
                                                nullable=True)
    bab: Mapped[str] = mapped_column(String(20), default='')
    kata_kunci: Mapped[str] = mapped_column(String(500), default='')
    #  'gratis' = pakai jatah · 'token' = sudah dipotong 1 Token Revisi.
    jenis: Mapped[str] = mapped_column(String(20), default='gratis')
    token: Mapped[int] = mapped_column(Integer, default=0)
    hasil_jumlah: Mapped[int] = mapped_column(Integer, default=0)
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)


# ── HITUNGAN SIKLUS (dekat DB — dipakai `app/jatah.py`) ──────────────────
def _sadar_naive(t: datetime) -> datetime:
    """Buang zona waktu → naive UTC (SQLite menyimpan naive).

    KENAPA: `_now()` (models.py) mengembalikan waktu AWARE (timezone.utc),
    sedangkan kolom DateTime SQLite membaca kembali sebagai NAIVE. Kalau
    keduanya dikurangkan → TypeError 'can't subtract offset-naive and
    offset-aware'. Fungsi ini menyeragamkan ke NAIVE supaya hitungan selisih
    waktu selalu sah, dari sumber mana pun.
    """
    if t is None:
        return t
    if isinstance(t, str):
        t = datetime.fromisoformat(t)
    if t.tzinfo is not None:
        t = t.astimezone(timezone.utc).replace(tzinfo=None)
    return t


def _mulai_siklus_berjalan(db, uid: int) -> datetime:
    """Awal siklus 7-hari yang SEDANG berjalan untuk user ini.

    Siklus berjalan = awal_pemakaian + n×7 hari (n sebesar mungkin tanpa
    melewati sekarang) ⇒ user dapat 2 gratis lagi tiap 7 hari berjalan.
    Belum pernah cari → siklus dianggap mulai SEKARANG.
    """
    from sqlalchemy import func as _f
    awal = (db.query(_f.min(PencarianManual.dibuat))
              .filter(PencarianManual.user_id == int(uid)).scalar())
    awal = _sadar_naive(awal)
    sekarang = _sadar_naive(_now())
    if awal is None:
        return sekarang
    n = max(0, (sekarang - awal).days // SIKLUS_HARI)
    return awal + timedelta(days=n * SIKLUS_HARI)


def terpakai_gratis(db, uid: int) -> int:
    """Berapa jatah gratis yang sudah dipakai di siklus berjalan."""
    from sqlalchemy import func as _f
    mulai = _mulai_siklus_berjalan(db, uid)
    return int((db.query(_f.count(PencarianManual.id))
                  .filter(PencarianManual.user_id == int(uid),
                          PencarianManual.jenis == 'gratis',
                          PencarianManual.dibuat >= mulai).scalar()) or 0)


def sisa_gratis(db, uid: int) -> int:
    """Sisa jatah gratis di siklus berjalan."""
    return max(0, JATAH_GRATIS - terpakai_gratis(db, uid))


def kapan_reset(db, uid: int) -> datetime:
    """Kapan jatah gratis kembali (akhir siklus berjalan)."""
    return _mulai_siklus_berjalan(db, uid) + timedelta(days=SIKLUS_HARI)


def pesan_jatah(sisa: int, reset: datetime) -> str:
    """Kalimat untuk user — HANGAT, memberi jalan keluar (gaya bahasa Bos).

    ⚠️ 06Okt26 (permintaan Bos): DILARANG pakai kata 'jatah' & 'gratis' di
    teks yang dibaca user. Sebutan resmi = 'Token Revisi'; yang tanpa biaya
    disebut 'tanpa Token'.
    """
    if sisa > 0:
        return (f'Kamu punya {sisa} pencarian tanpa Token untuk '
                f'{SIKLUS_HARI} hari ini ya — pakai sebaik mungkin.')
    return (f'Pencarian tanpa Token untuk {SIKLUS_HARI} hari ini sudah '
            f'terpakai. Pencarian berikutnya memakai {HARGA_TOKEN} Token '
            f'Revisi — pencarian tanpa Token kembali mulai {reset:%d %b} ya.')


def ringkas_jatah(db, uid: int) -> dict:
    """Ringkasan jatah untuk ditampilkan ke user."""
    sisa = sisa_gratis(db, uid)
    reset = kapan_reset(db, uid)
    return {'jatah': JATAH_GRATIS, 'terpakai': terpakai_gratis(db, uid),
            'sisa': sisa, 'siklus_hari': SIKLUS_HARI,
            'reset_pada': reset.isoformat(), 'harga_token': HARGA_TOKEN,
            'pesan': pesan_jatah(sisa, reset)}


# ══════════════════════════════════════════════════════════════════════════
# KOLABORASI PEMBIMBING (ACC Bos 23Sep26 — Tahap 1)
#
# POROS = PEMBIMBINGAN, BUKAN DOKUMEN. Kalau porosnya dokumen, mahasiswa
# mengganti naskah = catatan pembimbing hilang dari pandangan. Yang Bos mau:
# catatan menempel pada HUBUNGAN BIMBINGAN. Naskah berganti berkali-kali →
# catatan tetap ada.
#
# ⚠️ HANYA TABEL BARU. Tidak ada tabel lama yang diubah (tiang T2).
# ⚠️ RUANG 2 PEMBIMBING SUDAH DISIAPKAN (keputusan Bos: fitur nanti, tapi
#    ruangnya disiapkan sekarang) — lihat kolom `catatan_pembimbing.penulis_id`.
# ══════════════════════════════════════════════════════════════════════════

class Pembimbingan(Base):
    """SATU hubungan bimbingan: mahasiswa ↔ pembimbing (ACC Bos 23Sep26).

    Poros seluruh fitur kolaborasi. Dibuat saat mahasiswa menekan
    "Bagikan ke pembimbing". Berisi TOKEN yang jadi satu-satunya kunci
    masuk pembimbing.

    KEAMANAN (3 kunci pengaman yang Bos minta):
      1. HANYA LIHAT — pembimbing tidak pernah bisa mengubah naskah.
      2. LINK BERUMUR — kolom `kedaluwarsa` (7 atau 30 hari).
      3. BISA DICABUT — kolom `dicabut`.

    ⚠️ Token disimpan sebagai SIDIK SHA-256, bukan mentah. Kalau DB bocor,
    tidak ada pintu masuk yang langsung bisa dipakai.

    IDENTITAS PEMBIMBING = no HP atau email. TANPA verifikasi (keputusan Bos:
    "terlalu rumit untuk pembimbing"). Diisi SEKALI saat pembimbing pertama
    membuka link — bukan oleh mahasiswa. KENAPA begitu: kalau mahasiswa yang
    mengisi, dia bisa membuat identitas pembimbing palsu.
    """
    __tablename__ = 'pembimbingan'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    #  Pemilik naskah (mahasiswa). Selalu dipakai untuk memastikan mahasiswa
    #  hanya melihat bimbingannya sendiri — JANGAN pernah pakai user_id saat
    #  melayani pembimbing (dia tidak punya user_id).
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    #  Nama yang ditulis mahasiswa saat mengundang, mis. "Prof. Ahmad".
    nama: Mapped[str] = mapped_column(String(120), default='')
    #  Identitas pembimbing (HP atau email) — DIISI OLEH PEMBIMBING sendiri.
    identitas: Mapped[str] = mapped_column(String(160), default='', index=True)
    #  Kontak yang DIISI MAHASISWA saat membagikan (permintaan Bos 23Sep26:
    #  "Mahasiswa isi Nama dan No wa"). Untuk MENGIRIM link — nanti disambung
    #  ke webhook WA & email. ⚠️ BUKAN untuk login, dan JANGAN pernah
    #  ditampilkan ke pembimbing lain.
    wa: Mapped[str] = mapped_column(String(24), default='')
    email: Mapped[str] = mapped_column(String(160), default='')
    #  Sidik SHA-256 token link. Token mentah TIDAK PERNAH disimpan.
    token_sidik: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    #  Masa berlaku (7/30 hari) — dipakai halaman untuk menampilkan sisa waktu.
    hari: Mapped[int] = mapped_column(Integer, default=7)
    kedaluwarsa: Mapped[datetime] = mapped_column(DateTime, index=True)
    #  1 = dicabut mahasiswa. Link langsung mati (pengaman ke-3).
    dicabut: Mapped[int] = mapped_column(Integer, default=0, index=True)
    #  Kapan pembimbing pertama kali membuka link (bukti "sudah pernah masuk").
    dibuka_pada: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    # ═══ KUNCI NASKAH (Tahap 3.3, ACC Bos 06Okt26 "A") ═══
    #  Saat mahasiswa menyerahkan naskah ke penguji, semua sorotan pembimbing
    #  DISEMBUNYIKAN supaya skripsi tidak terlihat draft. Yang disimpan hanya
    #  waktu + siapa; catatan TIDAK dihapus (bisa dibuka lagi).
    #  DEFAULT NULL = belum pernah dikunci → perilaku lama tidak berubah.
    terkunci_pada: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    #  1 = dikunci oleh PEMBIMBING, 0 = dikunci oleh MAHASISWA (pemilik).
    terkunci_oleh: Mapped[int] = mapped_column(Integer, default=0)
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)
    diubah: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class BerkasPembimbingan(Base):
    """Naskah yang dibagikan dalam satu bimbingan (ACC Bos 23Sep26).

    KENAPA terpisah dari `files`: satu bimbingan bisa punya BANYAK naskah
    (banyak bab, banyak revisi). Mahasiswa menambahkan naskah ke bimbingan
    tanpa perlu membuat link baru — link tetap satu.

    ⚠️ `file_id` boleh NULL: bab bisa belum punya berkas tersendiri.
    Dengan begitu catatan tetap bisa menempel pada JUDUL bab, bukan memaksa
    ada berkas (menutup skenario "pembimbing menandai area kosong").
    """
    __tablename__ = 'pembimbingan_berkas'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pembimbingan_id: Mapped[int] = mapped_column(
        ForeignKey('pembimbingan.id'), index=True)
    file_id: Mapped[int] = mapped_column(
        ForeignKey('files.id'), nullable=True, index=True)
    #  Judul yang ditampilkan ke pembimbing, mis. "BAB I — Pendahuluan".
    judul: Mapped[str] = mapped_column(String(200), default='')
    #  SIDIK naskah saat dibagikan. Dipakai menjawab "naskah berubah atau
    #  belum?" secara JUJUR — aplikasi TIDAK boleh mengklaim "sudah diperbaiki".
    sidik: Mapped[str] = mapped_column(String(64), default='')
    #  Urutan tampil (BAB I, II, III…) — supaya tidak berubah tiap dibuka.
    urutan: Mapped[int] = mapped_column(Integer, default=0, index=True)
    catatan_kaki: Mapped[str] = mapped_column(String(200), default='')
    dibagikan_pada: Mapped[datetime] = mapped_column(DateTime, default=_now)
    diubah: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class CatatanPembimbing(Base):
    """Satu catatan pembimbing pada satu bagian naskah (ACC Bos 23Sep26).

    ═══ RANTAI REVISI ═══
    Revisi ke-2 pembimbing TIDAK menghidupkan sorotan lama (sorotan lama
    sudah mati — teksnya tidak ada lagi). Yang terjadi: catatan BARU di teks
    yang ADA SAAT ITU, diikat ke catatan sebelumnya lewat `induk_id`.
    Hasilnya: bukan 3 catatan lepas, tapi SATU RANTAI dengan 3 ronde.

    ═══ SOROTAN 3 KEADAAN ═══
    Sorotan = hiasan sementara. SUMBER KEBENARAN = tabel ini.
      UTUH     → teks cocok persis dengan `teks_asli`
      BERGESER → teks mirip (mahasiswa mengedit sedikit)
      HILANG   → teks tidak ditemukan; pembimbing tetap tahu dari sini
                 + tombol "Lihat teks asli" memakai `teks_asli`.
    KENAPA `teks_asli` DISIMPAN: supaya catatan menempel pada KENANGAN teks,
    bukan pada sorotan di layar. Sorotan bisa hilang; catatan tidak.

    ═══ RUANG 2 PEMBIMBING (disiapkan, fitur belum dibuka) ═══
    `penulis_id` = SIAPA yang menandai. Sekarang selalu 1 pembimbing, tapi
    kolomnya sudah ada → begitu fitur 2 pembimbing dibuka, TIDAK perlu
    bongkar tabel dan tidak ada data lama yang hilang.

    ═══ WARNA (3 saja — DILARANG teks bergaris/coret) ═══
      kuning = catatan pembimbing, belum ditindaklanjuti
      hijau  = pembimbing sudah bilang "Sudah oke"
      biru   = penanda pribadi mahasiswa (bukan milik pembimbing)
    """
    __tablename__ = 'catatan_pembimbing'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pembimbingan_id: Mapped[int] = mapped_column(
        ForeignKey('pembimbingan.id'), index=True)
    berkas_id: Mapped[int] = mapped_column(
        ForeignKey('pembimbingan_berkas.id'), nullable=True, index=True)
    #  SIAPA yang menandai (ruang 2 pembimbing). NULL = dari mahasiswa (biru).
    penulis_id: Mapped[int] = mapped_column(
        ForeignKey('pembimbingan.id'), nullable=True, index=True)
    #  RANTAI: menunjuk catatan sebelumnya pada masalah yang SAMA.
    induk_id: Mapped[int] = mapped_column(
        ForeignKey('catatan_pembimbing.id'), nullable=True, index=True)
    #  Ronde ke-berapa dalam rantai (1, 2, 3…). Baris ringkas memakai ini.
    ronde: Mapped[int] = mapped_column(Integer, default=1)
    #  Identitas bab, mis. 'BAB I' atau 'BAB I/subbab 1.2'.
    section_id: Mapped[str] = mapped_column(String(80), default='', index=True)
    #  Judul yang dibaca pembimbing, mis. "Pendahuluan".
    section_judul: Mapped[str] = mapped_column(String(200), default='')
    #  TEKS ASLI yang disorot — KENANGAN teks, bukan salinan naskah.
    teks_asli: Mapped[str] = mapped_column(Text, default='')
    #  Sidik teks asli → deteksi cepat UTUH / BERGESER / HILANG.
    sidik: Mapped[str] = mapped_column(String(64), default='', index=True)
    #  Posisi karakter saat disorot (perkiraan; berguna saat teks BERGESER).
    mulai: Mapped[int] = mapped_column(Integer, default=0)
    akhir: Mapped[int] = mapped_column(Integer, default=0)
    #  Sumber tanda: 1 = pembimbing, 0 = mahasiswa (penanda pribadi).
    dari_pembimbing: Mapped[int] = mapped_column(Integer, default=1)
    #  kuning | hijau | biru — HANYA 3 ini. Tidak ada coretan.
    warna: Mapped[str] = mapped_column(String(12), default='kuning')
    isi: Mapped[str] = mapped_column(Text, default='')
    #  Tautan yang dikirim pembimbing (tautan boleh, gambar/berkas menyusul).
    tautan: Mapped[str] = mapped_column(String(300), default='')
    #  ═══ LAMPIRAN GAMBAR (Tahap 2.2, ACC Bos 24Sep26) ═══
    #  Pembimbing kadang perlu MENUNJUKKAN sesuatu (tangkapan layar SPSS,
    #  contoh tabel, coretan) — bukan cuma menulis.
    #  `lampiran` = nama berkas DI DISK (bukan URL) → tidak bisa diakses
    #  langsung dari luar; harus lewat rute ber-token.
    #  `lampiran_nama` = nama asli dari komputer pembimbing (untuk ditampilkan).
    #  Kosong = tidak ada lampiran (aman untuk catatan lama).
    lampiran: Mapped[str] = mapped_column(String(120), default='')
    lampiran_nama: Mapped[str] = mapped_column(String(160), default='')
    #  Keadaan sorotan: utuh | bergeser | hilang.
    keadaan: Mapped[str] = mapped_column(String(12), default='utuh')
    #  Kapan pembimbing bilang "Sudah oke" (→ warna hijau).
    sudah_oke: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    #  ═══ LEWATI REVISI (Tahap 3.2, ACC Bos 24Sep26) ═══
    #  Mahasiswa boleh MELEWATI satu catatan, TAPI jejaknya tetap ada:
    #    dilewati = 1        → mahasiswa sudah menekan "Lewati revisi ini"
    #    dilewati_pada       → KAPAN (untuk track history)
    #    diaktifkan_pada     → KAPAN pembimbing membuka lagi catatan itu
    #    diaktifkan_oleh     → penulis_id pembimbing yang membuka lagi
    #
    #  ATURAN (dikte Bos, 24Sep26 — JANGAN diubah tanpa ACC):
    #    (1) "Revisi Dilewati" WAJIB muncul & tercatat di riwayat.
    #    (2) Mahasiswa TIDAK bisa membuka sendiri — hanya PEMBIMBING.
    #    (3) Begitu pembimbing buka lagi → tombol di dashboard mahasiswa
    #        HIDUP kembali → mahasiswa TETAP wajib mengerjakan.
    #    (4) Melewati BUKAN "selesai" — angka ringkasan tetap jujur.
    #
    #  ⚠️ KENAPA TIDAK PAKAI `warna`: `warna` = tanda dari PEMBIMBING
    #     (kuning/hijau/biru). Melewati = tindakan MAHASISWA. Kalau
    #     ditumpuk di `warna`, "sudah oke" pembimbing bisa hilang.
    #
    #  ⚠️ DATA LAMA AMAN: kolom baru → nilai default 0/NULL; baris lama
    #     tetap berarti "belum dilewati".
    dilewati: Mapped[int] = mapped_column(Integer, default=0, index=True)
    dilewati_pada: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    diaktifkan_pada: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    diaktifkan_oleh: Mapped[int] = mapped_column(Integer, default=0)

    #  SOFT-DELETE: 1 = tidak ditampilkan, TAPI TIDAK PERNAH dibuang.
    #  KENAPA: pembimbing kadang salah tulis; jejaknya harus tetap ada
    #  supaya mahasiswa tidak bisa mengklaim "saya tidak pernah diminta itu".
    dibuang: Mapped[int] = mapped_column(Integer, default=0, index=True)
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)
    diubah: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


# --- engine & session ---
engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False},
    echo=False,
)


@event.listens_for(engine, 'connect')
def _atur_sqlite(dbapi_conn, _):
    """WAL + foreign keys supaya SQLite aman untuk web."""
    cur = dbapi_conn.cursor()
    cur.execute('PRAGMA journal_mode=WAL')
    cur.execute('PRAGMA foreign_keys=ON')
    cur.execute('PRAGMA busy_timeout=8000')
    cur.close()


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)
    _migrasi_kolom()


def _migrasi_kolom() -> None:
    """ALTER TABLE idempoten untuk kolom yang ditambah setelah rilis awal.

    KENAPA manual: `create_all()` hanya membuat tabel BARU — tabel yang sudah ada
    tidak ditambahi kolom. SQLite juga tidak punya `ADD COLUMN IF NOT EXISTS`,
    jadi kita cek `PRAGMA table_info` dulu.

    Aman dijalankan berkali-kali (idempoten) dan aman untuk data lama
    (kolom nullable tanpa default wajib).
    """
    tambahan = {
        'transaksi': {
            # 12Sep26: batas berlaku QR untuk auto-expire LAZY.
            'kedaluwarsa': 'DATETIME',
        },
        'users': {
            # 14Sep26 (MASTER_PLAN §4.10): paket untuk kuota AI.
            # Default 'gratis' → user lama otomatis dapat paket gratis
            # (aman: mereka belum bayar, jadi memang tidak berhak AI).
            'paket': "VARCHAR(20) DEFAULT 'gratis'",
            # 26Sep26 (IDENTITAS COVER, ACC Bos): data mahasiswa untuk
            # halaman COVER naskah. DEFAULT '' / NULL supaya user LAMA
            # tidak rusak & boleh mengisi nanti (urutan ⑨ logo boleh
            # dilewati, sistem tetap jalan).
            'nama_lengkap': "VARCHAR(160) DEFAULT ''",
            'nim': "VARCHAR(40) DEFAULT ''",
            'nama_kampus': "VARCHAR(200) DEFAULT ''",
            'kota_kampus': "VARCHAR(80) DEFAULT ''",
            'fakultas': "VARCHAR(120) DEFAULT ''",
            'program_studi': "VARCHAR(120) DEFAULT ''",
            'berkas_logo_id': 'INTEGER',          # null = belum ada logo
            'pembimbing_1': "VARCHAR(160) DEFAULT ''",
            'pembimbing_2': "VARCHAR(160) DEFAULT ''",
        },
        'pembimbingan': {
            # 23Sep26 (Tahap 2 kolaborasi pembimbing): kontak yang diisi
            # MAHASISWA saat membagikan — dipakai untuk mengirim link.
            # Server mengisi '' sendiri (kolom NOT NULL di model), jadi
            # tambahkan dengan DEFAULT '' supaya baris lama tetap valid.
            'wa': "VARCHAR(24) DEFAULT ''",
            'email': "VARCHAR(160) DEFAULT ''",
            # 06Okt26 (Tahap 3.3 KUNCI NASKAH, ACC Bos "A"): saat mahasiswa
            # menyerahkan naskah ke penguji, sorotan pembimbing disembunyikan
            # supaya skripsi tidak terlihat draft. NULL = belum dikunci →
            # perilaku lama tidak berubah sama sekali.
            'terkunci_pada': 'DATETIME',
            'terkunci_oleh': 'INTEGER DEFAULT 0',
        },
        'catatan_pembimbing': {
            # 24Sep26 (Tahap 2.2 lampiran gambar): nama berkas di disk +
            # nama asli dari komputer pembimbing. DEFAULT '' supaya catatan
            # LAMA (yang belum punya lampiran) tetap valid.
            'lampiran': "VARCHAR(120) DEFAULT ''",
            'lampiran_nama': "VARCHAR(160) DEFAULT ''",
            # 24Sep26 (Tahap 3.2 LEWATI REVISI, ACC Bos): mahasiswa boleh
            # melewati satu catatan; pembimbing boleh mengaktifkannya lagi.
            # DEFAULT 0 / NULL supaya catatan LAMA tetap berarti
            # "belum dilewati" — tidak ada data yang berubah makna.
            'dilewati': 'INTEGER DEFAULT 0',
            'dilewati_pada': 'DATETIME',
            'diaktifkan_pada': 'DATETIME',
            'diaktifkan_oleh': 'INTEGER DEFAULT 0',
        },
        'versi_dokumen': {
            # 25Sep26 (C10 — bug "gear menghapus naskah"): versi tua ARSIP,
            # bukan dihapus. DEFAULT 0 supaya versi lama tetap "aktif".
            'diarsipkan': 'INTEGER DEFAULT 0',
        },
        'profil_dokumen': {
            # 26Sep26 (IDENTITAS COVER + PETA HALUS, ACC Bos):
            # identitas boleh ditimpa per naskah (default dari akun);
            # peta = hasil peta halus + sidik naskah (agar tidak panggil
            # AI berulang untuk naskah yang sama).
            'nama_lengkap': "VARCHAR(160) DEFAULT ''",
            'nim': "VARCHAR(40) DEFAULT ''",
            'nama_kampus': "VARCHAR(200) DEFAULT ''",
            'kota_kampus': "VARCHAR(80) DEFAULT ''",
            'fakultas': "VARCHAR(120) DEFAULT ''",
            'program_studi': "VARCHAR(120) DEFAULT ''",
            'berkas_logo_id': 'INTEGER',
            'asal_naskah': "VARCHAR(20) DEFAULT ''",   # 'eduai' | 'user'
            'peta_json': 'TEXT',
            'peta_sidik': "VARCHAR(64) DEFAULT ''",
            'peta_dibuat': 'DATETIME',
            # 26Sep26 (STANDAR PENULISAN, ACC Bos): panduan penulisan
            # kampus yang diunggah user per naskah (JSON hasil ekstraksi).
            # '' = belum ada → pakai ATURAN_BAKU app/standar_penulisan.py.
            'panduan_json': 'TEXT',
            # 06Okt26 (JURNAL/REFERENSI, ACC Bos Opsi A): daftar artikel
            # jurnal per naskah + penanda BAB (JSON) — meniru pola peta_json.
            'jurnal_json': 'TEXT',
            'jurnal_sidik': "VARCHAR(64) DEFAULT ''",
        },
    }
    with engine.connect() as c:
        for tabel, kolom in tambahan.items():
            ada = {r[1] for r in c.exec_driver_sql(f'PRAGMA table_info({tabel})')}
            if not ada:
                continue                      # tabel belum ada -> create_all urus
            for nama, tipe in kolom.items():
                if nama not in ada:
                    c.exec_driver_sql(f'ALTER TABLE {tabel} ADD COLUMN {nama} {tipe}')
                    log.info('[migrasi] %s.%s ditambahkan', tabel, nama)
        c.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SaldoToken(Base):
    """BUKU BESAR (ledger) SALDO TOKEN — SATU KANTONG (ACC Bos 26Sep26).

    KENAPA LEDGER, bukan satu kolom angka:
      Bos minta "apapun upgrade paketnya dan berapa kali beli AddOn masuknya
      ke saldo semua" — jadi setiap PEMASUKAN harus punya asal-usul yang bisa
      diaudit (dari paket mana / AddOn mana / tanggal berapa). Satu kolom
      angka tidak bisa menjawab "token saya dari mana?" saat user bertanya.

    `sisa` = saldo berjalan SETELAH baris ini (memudahkan tampilan & audit).

    jumlah > 0 = pemasukan · jumlah < 0 = pemakaian.
    """
    __tablename__ = 'saldo_token'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True,
                                         nullable=False)
    jumlah: Mapped[int] = mapped_column(Integer, default=0)   # +masuk / -pakai
    sisa: Mapped[int] = mapped_column(Integer, default=0)     # saldo sesudah
    sumber: Mapped[str] = mapped_column(String(40), default='', index=True)
    #  ↑ 'paket:penulis' | 'upgrade:penulis|peneliti' | 'addon:ai' |
    #    'pakai:kerangka' | 'kembali:kerangka' | 'awal:migrasi'
    catatan: Mapped[str] = mapped_column(String(200), default='')
    order_id: Mapped[str] = mapped_column(String(100), default='', index=True)
    dibuat: Mapped[datetime] = mapped_column(DateTime, default=_now)
