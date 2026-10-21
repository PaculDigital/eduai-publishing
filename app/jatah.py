"""JATAH PENCARIAN MANUAL — 2× gratis per MINGGU, lewat itu 1 token (06Okt26).

📌 PUTUSAN BOS 06Okt26 (terkunci):
   · Yang dihitung = Pencarian MANUAL saja (pencarian AI GRATIS sampai kerangka)
   · Harga = 1 Token Revisi per pencarian manual
   · Siklus = 7 hari, dihitung sejak AWAL PEMAKAIAN user (bukan sejak daftar)
   · Jatah gratis = 2× per siklus 7 hari
   · Batas per USER (bukan per naskah/workspace) — sesuai putusan pagar
   · Dihitung di SERVER (DB), bukan di browser

📌 POLA YANG DIIKUTI (tidak bikin mesin baru):
   · Tabel jejak `pencarian_manual` (di models.py, meniru `pembatalan_kuota`)
   · Pesan tolak: HANGAT, memberi jalan keluar (aturan gaya bahasa Bos)
   · Dompet: SATU pintu — `kuota.potong_banyak()` (tidak ada dompet paralel)

📌 KENAPA 7 HARI BERJALAN (bukan "minggu kalender"):
   Siklus mulai dari pemakaian PERTAMA user. Kalau pakai minggu kalender
   (Senin–Minggu), user yang mulai hari Jumat hanya dapat 2 hari.

📌 PEMISAHAN TUGAS:
   · `app/models.py` — Tabel `PencarianManual` + hitungan siklus (dekat DB)
   · `app/jatah.py`  — Pintu keputusan (boleh cari? gratis atau token?)
"""
from __future__ import annotations

import logging

from .models import (HARGA_TOKEN, JATAH_GRATIS, PencarianManual, SIKLUS_HARI,
                     kapan_reset, pesan_jatah, ringkas_jatah, sisa_gratis,
                     terpakai_gratis)

log = logging.getLogger('eduai.jatah')

SUMBER_TOKEN = 'cari_manual'


def ringkas(db, uid: int) -> dict:
    """Ringkasan jatah untuk ditampilkan ke user (nada hangat)."""
    return ringkas_jatah(db, uid)


def boleh_cari(db, uid: int) -> dict:
    """Cek apakah user boleh cari manual — dan dengan cara apa.

    Return {'boleh', 'jenis' ('gratis'|'token'), 'sisa', 'token', ...}.
    TIDAK memotong token (pemotongan dilakukan pemanggil lewat kuota).
    """
    sisa = sisa_gratis(db, uid)
    if sisa > 0:
        return {'boleh': True, 'jenis': 'gratis', 'sisa': sisa,
                'token': 0, 'r': ringkas(db, uid)}
    return {'boleh': True, 'jenis': 'token', 'sisa': 0,
            'token': HARGA_TOKEN, 'r': ringkas(db, uid)}


def catat(db, uid: int, kata_kunci: str, jenis: str = 'gratis',
          file_id: int | None = None, bab: str = '',
          hasil_jumlah: int = 0, token: int = 0) -> PencarianManual:
    """Catat pencarian. TIDAK commit — pemanggil yang commit."""
    b = PencarianManual(user_id=int(uid), kata_kunci=(kata_kunci or '')[:500],
                        jenis=jenis, file_id=file_id, bab=str(bab or ''),
                        hasil_jumlah=int(hasil_jumlah or 0),
                        token=int(token or 0))
    db.add(b)
    return b


def pesan_tidak_cukup_saldo() -> str:
    """Pesan hangat saat token tidak cukup (memberi jalan keluar).

    ⚠️ 06Okt26 (permintaan Bos): tanpa kata 'jatah' & 'gratis'.
    """
    return (f'Untuk mencari lagi, perlu {HARGA_TOKEN} Token Revisi — '
            'saldomu belum cukup. Kamu bisa isi Token Revisi dulu, atau '
            'tunggu pencarian tanpa Token kembali ya.')


__all__ = ['JATAH_GRATIS', 'SIKLUS_HARI', 'HARGA_TOKEN', 'SUMBER_TOKEN',
           'ringkas', 'boleh_cari', 'catat', 'pesan_tidak_cukup_saldo',
           'sisa_gratis', 'terpakai_gratis', 'kapan_reset', 'pesan_jatah',
           'PencarianManual']
