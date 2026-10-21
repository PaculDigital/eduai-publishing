"""LAMPIRAN PEMBIMBING (Tahap 2.2, ACC Bos 24Sep26).

KEPUTUSAN BOS:
  · Jenis: GAMBAR + PDF + Word/Excel — bebas apa saja.
  · Fungsi: PELENGKAP KOMENTAR — pembimbing menunjuk sumber/contoh
    yang dia maksud (untuk MATA mahasiswa, bukan untuk AI).
  · AI baca lampiran? NANTI dibahas di Tahap 4 (pembimbing pakai AI).

KENAPA modul terpisah:
  · Lampiran pembimbing BUKAN berkas mahasiswa. Disimpan di folder sendiri
    supaya TIDAK menghitung kuota storage mahasiswa dan tidak muncul di
    "Naskah Saya".
  · Nama berkas dibuat SERVER (acak), BUKAN dari user — supaya tidak ada
    celah `../../` atau nama berkas jahat.

ATURAN AMAN (sengaja ketat):
  1. Hanya jenis berkas yang dikenal (lihat EKSTENSI_LAMPIRAN).
  2. Batas ukuran 10 MB — ini catatan, bukan naskah.
  3. Nama di disk = token acak + ekstensi. Nama asli hanya untuk DITAMPILKAN.
  4. Berkas diakses lewat rute ber-token, TIDAK bisa ditebak.
"""

from __future__ import annotations

import logging
import secrets
from pathlib import Path

from fastapi import UploadFile

log = logging.getLogger('eduai.pembimbing.lampiran')

#  Folder terpisah dari UPLOAD_DIR (berkas mahasiswa).
#  ⚠️ JANGAN pakai UPLOAD_DIR — nanti ikut hitungan kuota mahasiswa.
LAMPIRAN_DIR = Path('/app/data/lampiran_pembimbing')

#  ── Jenis berkas yang BOLEH (ACC Bos 24Sep26: gambar + PDF + Word/Excel) ──
#  Semua yang di sini hanya DILIHAT/DIBACA — tidak pernah dieksekusi.
#  ⚠️ 10 Okt 2026 (putusan Bos "A — standard aplikasi"): FORMAT LAMA OFFICE
#     (.doc/.xls/.ppt) DIBUANG dari sini juga. Alasan: standard aplikasi —
#     kalau .doc dilarang di pintu unggah tapi boleh di lampiran, pesannya
#     jadi tidak konsisten; dan format biner lama tidak bisa dibaca aman.
EKSTENSI_LAMPIRAN = {
    #  Gambar
    '.png', '.jpg', '.jpeg', '.webp', '.gif',
    #  Dokumen (hanya format BARU/OOXML)
    '.pdf', '.docx', '.xlsx', '.pptx',
    '.txt', '.csv', '.rtf', '.odt', '.ods',
}

#  Yang perlu DITAMPILKAN sebagai gambar di halaman tinjau (thumbnail).
EKSTENSI_GAMBAR = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}

#  Batas ukuran: catatan, bukan naskah. 10 MB cukup untuk PDF contoh.
MAKS_LAMPIRAN = 10 * 1024 * 1024

_ALFABET = 'abcdefghijklmnopqrstuvwxyz0123456789'


def _nama_aman(nama: str) -> str:
    """Nama tampilan: buang jalur folder + batasi panjang.

    ⚠️ Dipakai HANYA untuk ditampilkan. TIDAK dipakai sebagai nama di disk.
    """
    n = (nama or 'lampiran').replace('\\', '/').split('/')[-1]
    n = ''.join(c for c in n if c.isprintable() and c not in '<>"')
    return n.strip()[:160] or 'lampiran'


def ekstensi_aman(nama: str) -> str:
    """Ekstensi berkas dari NAMA ASLI user (dipakai untuk menampilkan jenis)."""
    return Path(_nama_aman(nama)).suffix.lower()


def simpan(berkas: UploadFile) -> tuple[str, str]:
    """Simpan satu lampiran. Return (nama_di_disk, nama_tampilan).

    Melempar ValueError kalau jenis/ukuran tidak sah — PEMANGGIL yang
    memutuskan mau menampilkan pesan apa.
    """
    ekst = Path(berkas.filename or '').suffix.lower()
    if ekst not in EKSTENSI_LAMPIRAN:
        raise ValueError(
            'Jenis berkas belum didukung. Pakai gambar, PDF, '
            'Word, Excel, atau PowerPoint.')
    isi = berkas.file.read()
    if not isi:
        raise ValueError('Berkas kosong.')
    if len(isi) > MAKS_LAMPIRAN:
        raise ValueError(
            f'Berkas terlalu besar (maks {MAKS_LAMPIRAN // 1024 // 1024} MB).')
    #  Cek tanda tangan berkas — jangan percaya ekstensi saja.
    if not _tanda_cocok(isi, ekst):
        raise ValueError('Isi berkas tidak cocok dengan namanya.')

    LAMPIRAN_DIR.mkdir(parents=True, exist_ok=True)
    #  Nama SERVER: token acak, tidak bisa ditebak dari luar.
    nama_disk = ''.join(secrets.choice(_ALFABET) for _ in range(24)) + ekst
    (LAMPIRAN_DIR / nama_disk).write_bytes(isi)
    log.info('[lampiran] disimpan %s (%s byte)', nama_disk, len(isi))
    return nama_disk, _nama_aman(berkas.filename or 'lampiran')


#  Tanda tangan berkas (magic bytes) per kelompok jenis.
_TANDA = {
    'png': [b'\x89PNG\r\n\x1a\n'],
    'jpg': [b'\xff\xd8\xff'],
    'gif': [b'GIF87a', b'GIF89a'],
    'pdf': [b'%PDF'],
    'zip': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],   # docx/xlsx/pptx/odt
    #  ⚠️ 10 Okt 2026: tanda tangan 'doc' (OLE: \xd0\xcf\x11\xe0) DIBUANG —
    #     format lama Office tidak lagi diizinkan (putusan Bos: standard aplikasi).
    'rtf': [b'{\\rtf'],
    'teks': None,                                             # txt/csv: apa saja
}


def _kelompok(ekst: str) -> str:
    if ekst in {'.png'}:
        return 'png'
    if ekst in {'.jpg', '.jpeg'}:
        return 'jpg'
    if ekst in {'.gif'}:
        return 'gif'
    if ekst == '.pdf':
        return 'pdf'
    if ekst == '.webp':
        return 'webp'
    if ekst in {'.docx', '.xlsx', '.pptx', '.odt', '.ods'}:
        return 'zip'
    #  ⚠️ 10 Okt 2026: cabang '.doc/.xls/.ppt' DIBUANG — format lama tidak lagi
    #     diizinkan di mana pun (putusan Bos A: "standard aplikasi").
    #     Kalau tetap ada cabang 'doc', tanda tangan OLE akan dicocokkan untuk
    #     berkas yang tak mungkin masuk ⇒ kode mati.
    if ekst == '.rtf':
        return 'rtf'
    return 'teks'


def _tanda_cocok(isi: bytes, ekst: str) -> bool:
    """Apakah 12 byte pertama cocok dengan jenis yang diklaim?"""
    kel = _kelompok(ekst)
    if kel == 'webp':
        return isi[:4] == b'RIFF' and isi[8:12] == b'WEBP'
    if kel == 'teks':
        return True                       # txt/csv tidak punya tanda tangan
    for tanda in (_TANDA.get(kel) or []):
        if isi[:len(tanda)] == tanda:
            return True
    return False


def jalur(nama_disk: str) -> Path | None:
    """Jalur berkas lampiran. None kalau namanya tidak sah/tidak ada.

    ⚠️ Tolak nama yang memuat '/' atau '..' — cegah keluar folder.
    """
    n = (nama_disk or '').strip()
    if not n or '/' in n or '\\' in n or '..' in n:
        return None
    p = LAMPIRAN_DIR / n
    return p if p.is_file() else None


def apakah_gambar(nama_disk: str) -> bool:
    """Apakah lampiran ini gambar (bisa ditampilkan sebagai <img>)?"""
    return Path(nama_disk or '').suffix.lower() in EKSTENSI_GAMBAR
