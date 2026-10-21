"""DOKUMEN BARU — bikin naskah kosong atas nama user (ACC Bos 26Sep26, OPSI D).

=== KENAPA BEGINI (bukan panggilan API OnlyOffice) ===
Bos bertanya: "Pakai panggilan api buat dokumen baru kan bisa?"

JAWABAN TERUKUR (26Sep26):
  · ConvertService.ashx OnlyOffice HIDUP, TAPI untuk membuat berkas
    ia HARUS mengunduh sendiri berkasnya lewat URL publik.
    Diuji → `{"error":-8}` (= URL masukan tidak terjangkau), karena
    `oo-converter` tidak bisa melihat `127.0.0.1:8000` milik eduai-app.
  · Jadi jalur API = 2 perjalanan + rawan meleset. TIDAK PERLU.
  · Yang SUDAH ADA & TERBUKTI: alur unggah di `app/main.py` sudah
    menyimpan berkas + mendaftarkan baris `files` (baris 527-536).
    Untuk dokumen baru, cukup SALIN TEMPLAT lalu daftarkan.

TEMPLAT: `app/templat/naskah-baru.docx` — template resmi OnlyOffice
(document-templates/new/default/new.docx, 6.940 byte, docx SAH:
14 berkas, `word/document.xml` ada). Disimpan di repo supaya TIDAK
bergantung container lain.

=== URUTAN (Opsi D yang Bos putuskan) ===
  1. User klik "Mulai baru"
  2. Server buat dokumen kosong  ← modul ini
  3. Baris `files` terbentuk → kartu profil (jenjang/bidang/jenis/judul)
     langsung punya tempat → 4 langkah TERSIMPAN normal
  4. User lihat "naskahku sudah ada", tinggal EduAi isi kerangkanya
"""
from __future__ import annotations

import secrets
import shutil
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from .config import UPLOAD_DIR
from .models import FileBerkas, User

#  Templat ikut dibawa ke image (app/ di-COPY oleh Dockerfile).
TEMPLAT = Path(__file__).resolve().parent / 'templat' / 'naskah-baru.docx'

#  Nama berkas yang user lihat (bukan nama simpan internal).
NAMA_TAMPIL = 'Naskah Baru.docx'


def templat_ada() -> bool:
    """Cek templat ada & bisa dibaca (dipakai pagar sebelum membuat)."""
    return TEMPLAT.is_file() and TEMPLAT.stat().st_size > 1000


def buat_dokumen_baru(db: Session, u: User,
                      nama: str = '', folder_id: int | None = None
                      ) -> dict[str, Any]:
    """Bikin dokumen kosong untuk user → balas info berkas baru.

    PAGAR (jangan pernah bikin baris `files` tanpa berkas nyata di disk —
    itu yang membuat kartu profil menunjuk dokumen hantu):
      1. Templat WAJIB ada → kalau tidak, tolak dengan pesan jelas.
      2. Berkas ditulis DULU ke disk, baru `db.commit()`.
      3. `nama_simpan` unik (token_hex) — pola SAMA dengan alur unggah.
      4. Kalau commit gagal → berkas di disk DIBUANG (jangan tinggalkan
         sampah yatim di folder user).
    """
    if not templat_ada():
        raise FileNotFoundError(
            'Templat naskah baru tidak ditemukan di server '
            f'({TEMPLAT}). Dokumen baru belum bisa dibuat.')

    # ── Nama tampil: minta user, atau pakai bawaan ─────────────────────
    nama_asli = (nama or '').strip() or NAMA_TAMPIL
    if not nama_asli.lower().endswith('.docx'):
        nama_asli += '.docx'
    #  Jangan biarkan user menuliskan garis miring (bikin folder aneh).
    nama_asli = nama_asli.replace('/', '-').replace('\\', '-')[:120]

    # ── Tulis berkas ke folder user (isolasi per user) ─────────────────
    dir_unggah = UPLOAD_DIR / str(u.id)
    dir_unggah.mkdir(parents=True, exist_ok=True)
    nama_simpan = f'{secrets.token_hex(8)}.docx'
    tujuan = dir_unggah / nama_simpan
    shutil.copyfile(TEMPLAT, tujuan)

    ukuran = tujuan.stat().st_size

    # ── Daftarkan di tabel `files` ─────────────────────────────────────
    fb = FileBerkas(
        user_id=u.id,
        nama=nama_asli,
        nama_simpan=nama_simpan,
        ukuran=ukuran,
        tipe=('application/vnd.openxmlformats-officedocument'
              '.wordprocessingml.document'),
        folder_id=folder_id,
    )
    try:
        db.add(fb)
        db.commit()
        db.refresh(fb)
    except Exception:
        db.rollback()
        #  jangan tinggalkan berkas yatim yang tidak tercatat
        try:
            tujuan.unlink(missing_ok=True)
        except Exception:                                        # noqa: BLE001
            pass
        raise

    return {
        'ok': True,
        'file_id': fb.id,
        'nama': fb.nama,
        'nama_simpan': fb.nama_simpan,
        'ukuran': ukuran,
        'pesan': f'Naskah baru "{fb.nama}" berhasil dibuat. '
                 'Selanjutnya isi langkah awal, lalu EduAi susun kerangkanya.',
    }
