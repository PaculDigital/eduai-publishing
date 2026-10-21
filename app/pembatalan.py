"""ATURAN PEMBATALAN KUOTA SAAT ROLLBACK NASKAH — Opsi C (ACC Bos 17Sep26).

════════════════════════════════════════════════════════════════════════════
 MASALAH YANG DITUTUP
════════════════════════════════════════════════════════════════════════════
 User revisi (kuota terpotong) → lalu ROLLBACK naskah. Kalau kuota selalu
 dikembalikan, user bisa MENGGILING GRATIS:

     revisi → salin isinya ke tempat lain → rollback → kuota balik → ulangi

 AI bekerja 10×, user membayar 0×. Bos yang menangkap lubang ini:
 *"Jika pilih B bagaimana kalo user rollback terus saya rugi ai bekerja
 terus, nanti rollback lagi."*

════════════════════════════════════════════════════════════════════════════
 ATURAN (OPSI C — keputusan Bos)
════════════════════════════════════════════════════════════════════════════
Kuota dibalikkan HANYA bila KETIGA syarat ini terpenuhi:

  1. HASIL BELUM DIBUKA      → `proses_ai.dibaca == 0`
     Kalau sudah dibuka, mahasiswa sudah melihat isinya = sudah dapat manfaat.

  2. HASIL BELUM DITERAPKAN  → versi hasil revisi belum `terpakai`
     Kalau sudah diterapkan ke .docx, naskah sudah berubah = tidak bisa dibatal.

  3. BELUM PAKAI HAK INI untuk naskah ini HARI INI
     → maksimal 1× per NASKAH (bukan per akun) per hari.

PAGAR TAMBAHAN:
  · JEDA 20 MENIT sejak revisi selesai. Lewat itu → hak hangus (mahasiswa
    pasti sudah membaca isinya kalau butuh lebih lama).
  · Rollback harus ke versi SEBELUM revisi itu. Kalau mahasiswa memilih
    versi SESUDAHnya, artinya dia memang mau pakai hasilnya → kuota tetap.

YANG SELALU DILAKUKAN:
  · Naskah SELALU dikembalikan (itu hak mahasiswa, tidak pernah ditahan).
  · Notifikasi SELALU dikirim, apa pun hasilnya (permintaan Bos).
  · Kuota TIDAK PERNAH dikembalikan lebih dari yang benar-benar dipotong.

⚠️ PELAJARAN YANG DIPEGANG (16Sep26): JANGAN deteksi kondisi dengan
   cocok-cocokan kata di pesan. Di sini semua penanda STRUKTURAL —
   kolom DB, waktu, dan jumlah baris — bukan teks.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.orm import Session

log = logging.getLogger(__name__)

#  ── Angka aturan (di sini saja — jangan disebar ke UI) ────────────────────
JEDA_MENIT = 20          # jendela waktu sejak revisi selesai
MAKS_HARI_INI = 1        # maksimal 1× per naskah per hari


def _hari_ini() -> datetime:
    """Awal hari (00:00) dalam UTC — dasar hitungan "hari ini"."""
    n = datetime.utcnow()
    return n.replace(hour=0, minute=0, second=0, microsecond=0)


def boleh_dibalikkan(db: Session, user_id: int, file_id: int,
                     kode_proses: str) -> tuple[bool, str, int]:
    """Periksa apakah kuota revisi LAYAK dibalikkan.

    Kembalikan (boleh: bool, alasan: str, jumlah: int).
    `alasan` HANYA untuk teknisi/log — JANGAN ditampilkan ke mahasiswa.

    Urutan pemeriksaan sengaja dari yang paling murah & paling jelas.
    """
    from .models import ProsesAI, VersiDokumen, PembatalanKuota

    #  ── Syarat 3b: hari ini sudah pernah pakai hak ini untuk naskah ini? ──
    #  Diperiksa LEBIH DULU karena ini pagar anti-penyalahgunaan yang utama.
    try:
        sudah = db.execute(
            select(func.count(PembatalanKuota.id)).where(
                PembatalanKuota.user_id == user_id,
                PembatalanKuota.file_id == file_id,
                PembatalanKuota.jumlah_kembali > 0,
                PembatalanKuota.dibuat >= _hari_ini(),
            )
        ).scalar_one()
        if sudah >= MAKS_HARI_INI:
            return False, 'sudah_pakai_hak_hari_ini', 0
    except Exception as e:                                        # noqa: BLE001
        log.warning('[batal] gagal hitung riwayat pembatalan: %s', e)
        return False, 'galat_hitung_riwayat', 0

    #  ── Cari prosesnya ──
    p = db.execute(
        select(ProsesAI).where(
            ProsesAI.kode == kode_proses,
            ProsesAI.user_id == user_id,
        )
    ).scalar_one_or_none()
    if p is None:
        return False, 'proses_tidak_ada', 0
    if p.status != 'selesai':
        return False, f'proses_{p.status}', 0

    #  ── Syarat 1: hasil belum pernah dibuka? ──
    if (p.dibaca or 0) != 0:
        return False, 'hasil_sudah_dibuka', 0

    #  ── Pagar: jeda 20 menit sejak revisi selesai ──
    if p.selesai is None:
        return False, 'waktu_selesai_kosong', 0
    lewat = datetime.utcnow() - p.selesai
    if lewat > timedelta(minutes=JEDA_MENIT):
        return False, 'lewat_jeda_waktu', 0

    #  ── Syarat 2: hasil belum diterapkan ke dokumen? ──
    #  Versi hasil revisi yang sudah `terpakai=True` berarti naskah sudah
    #  berubah nyata — pembatalan tidak lagi jujur.
    try:
        dipakai = db.execute(
            select(func.count(VersiDokumen.id)).where(
                VersiDokumen.file_id == file_id,
                VersiDokumen.sumber == 'ai',
                VersiDokumen.terpakai.is_(True),
                VersiDokumen.dibuat >= (p.dibuat or p.selesai),
            )
        ).scalar_one()
        if dipakai > 0:
            return False, 'hasil_sudah_diterapkan', 0
    except Exception as e:                                        # noqa: BLE001
        log.warning('[batal] gagal periksa versi terpakai: %s', e)
        return False, 'galat_periksa_versi', 0

    #  ── Berapa yang boleh dibalikkan? ──
    #  Tidak lebih dari yang benar-benar dipotong untuk proses ini.
    jumlah = max(0, int(p.token_revisi or 0))
    if jumlah <= 0:
        #  Kalau token_revisi tidak tercatat, pakai jumlah bagian sebagai
        #  perkiraan konservatif (1 bagian = 1 Token Revisi).
        jumlah = max(1, int(p.jumlah_bagian or 1))
    return True, 'boleh', jumlah


def catat_pembatalan(db: Session, user_id: int, file_id: int,
                     kode_proses: str, jumlah_kembali: int,
                     alasan: str) -> None:
    """Simpan jejak pembatalan — SELALU aman, tidak pernah melempar.

    ⚠️ `db` TIDAK di-commit di sini; pemanggil yang memutuskan.
    """
    try:
        from .models import PembatalanKuota
        db.add(PembatalanKuota(
            user_id=user_id, file_id=file_id, kode_proses=kode_proses,
            jumlah_kembali=int(jumlah_kembali or 0), alasan=alasan or '',
        ))
        db.flush()
    except Exception as e:                                        # noqa: BLE001
        log.warning('[batal] catat jejak gagal: %s', e)
        try:
            db.rollback()
        except Exception:                                         # noqa: BLE001
            pass
