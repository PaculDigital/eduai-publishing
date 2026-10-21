"""BACA LAMPIRAN PEMBIMBING untuk prompt AI mahasiswa (ACC Bos 27Sep26).

Pertanyaan Bos: "kalau pembimbing menyertakan gambar/PDF/docx di komentar,
apakah AI penulis bisa membacanya?" — SEBELUMNYA TIDAK (komentar dikirim
teks saja). Sekarang:

  · PDF/docx/xlsx/txt → teks via `_teks_dari_berkas` (parser yang SAMA
    dengan jalur unggah naskah — TIDAK bikin parser kedua) + batas
    LAMPIRAN_TEKS_MAKS agar prompt tidak meledak.
  · Gambar (png/jpg/webp/gif) → dikompres + dipangkas → base64 data URL,
    dikirim sebagai `image_url` lewat combo `EduAi` (9router otomatis
    mengalihkan ke model vision — TERBUKTI 27Sep26, alat
    _sketsa/uji_vision_9router.py: mimo-v2.6-flash 4,7 dtk baca teks
    gambar betul).

Semua fungsi JUJUR GAGAL: berkas hilang/rusak → balik '' (lampiran tidak
membuat revisi GAGAL — jalan keluar selalu ada).
"""
from __future__ import annotations

import base64
import io
import logging
import re

from PIL import Image

from . import lampiran_pembimbing as LP

log = logging.getLogger('uvicorn.error')

#  Batas teks lampiran di prompt (≈2.500 token) — cukup utk contoh tabel/
#  jurnal, prompt revisi tetap ringan (hemat token, aturan Bos).
LAMPIRAN_TEKS_MAKS = 10_000

#  Gambar maksimum 1.600 px sisi terpanjang + JPEG kualitas 80 → biasanya
#  100-300 KB → 40-100 ribu token gambar jauh di bawah batas model.
GAMBAR_SISI_MAKS = 1600
GAMBAR_KUALITAS = 80
GAMBAR_BYTE_MAKS = 600_000          # setelah kompres masih kecil? teruskan.

GAMBAR_EKST = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
#  ⚠️ 10 Okt 2026 (putusan Bos "A: standard aplikasi"): '.doc'/'.xls'
#  (format lama Office) DIBUANG — berkas itu tak mungkin sampai ke sini.
TEKS_EKST = {'.pdf', '.docx', '.txt', '.md', '.csv', '.xlsx'}


def baca_teks(nama_disk: str) -> str:
    """Teks isi lampiran dokumen. '' = tak bisa dibaca (JANGAN raise)."""
    p = LP.jalur(nama_disk or '')
    if p is None:
        return ''
    try:
        from .ai import _teks_dari_berkas          # noqa: PLC0415 — parser TUNGGAL
        teks = (_teks_dari_berkas(p, p.name) or '').strip()
    except Exception:                              # noqa: BLE001 — berkas rusak
        log.warning('[lampiran-ai] gagal ekstrak teks %s', nama_disk)
        return ''
    return teks[:LAMPIRAN_TEKS_MAKS]


def data_url_gambar(nama_disk: str) -> str:
    """Gambar → data URL base64 siap `image_url`. '' = gagal (jangan raise)."""
    p = LP.jalur(nama_disk or '')
    if p is None:
        return ''
    try:
        img = Image.open(p)
        img.load()
        #  GIF animasi → ambil frame pertama saja (cukup sebagai contoh).
        img = img.convert('RGB') if img.mode not in ('RGB', 'L') else img
        w, h = img.size
        sisi = max(w, h)
        if sisi > GAMBAR_SISI_MAKS:
            rasio = GAMBAR_SISI_MAKS / sisi
            img = img.resize((max(1, int(w * rasio)),
                              max(1, int(h * rasio))))
        buf = io.BytesIO()
        img.save(buf, 'JPEG', quality=GAMBAR_KUALITAS)
        data = buf.getvalue()
        if len(data) > GAMBAR_BYTE_MAKS:           # kualitas diturunkan 1×
            buf = io.BytesIO()
            img.save(buf, 'JPEG', quality=55)
            data = buf.getvalue()
        return 'data:image/jpeg;base64,' + base64.b64encode(data).decode()
    except Exception:                              # noqa: BLE001 — rusak
        log.warning('[lampiran-ai] gagal baca gambar %s', nama_disk)
        return ''


def jenis(nama_disk: str) -> str:
    """'gambar' | 'teks' | '' (tidak dikenal)."""
    ekst = re.sub(r'^.*(\.[a-z0-9]+)$', r'\1', (nama_disk or '').lower())
    if ekst in GAMBAR_EKST:
        return 'gambar'
    if ekst in TEKS_EKST:
        return 'teks'
    return ''