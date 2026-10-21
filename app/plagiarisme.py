"""Uji Plagiarisme (ACC Bos 16 Okt 2026) — PEMASANGAN, bukan mesin baru.

Satu perintah: naskah EduAi → 1 berkas PDF (naskah + stabilo + laporan + watermark).

RANCANGAN (nol mesin/tabel/dompet baru):
  ① Naskah  : dibaca dari `berkas` (berkas_id) — SATU gerbang upload (putusan Bos)
  ② Mesin   : `app/uji_mirip.py` → merakit `scripts/similarity_precheck.py`
  ③ Gratis  : 1× per naskah (dijaga sidik SHA-256 + tabel `pencarian_manual`)
  ④ Token   : `kuota.potong_banyak()` — SUDAH ADA (8 token, putusan Bos)
  ⑤ Mesin pencari belum ada (Google blokir VPS) ⇒ GRATIS pakai mode contoh;
              BERBAYAR ditahan sampai Bos pasang API key.

⚠️ ATURAN BOS: "Naskah: hanya dari EduAi (1 gerbang upload)". Jadi kita TIDAK
   menerima teks tempelan — hanya `berkas_id` milik user itu sendiri.
"""
from __future__ import annotations

import hashlib
import html as _html
import os
import re
import zipfile
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import kuota

#  ── PUTUSAN BOS (16 Okt 2026) — TERKUNCI, jangan diubah sendiri ──
BIAYA_TOKEN = 8          # 8 token per cek
PEMBANDING = 11          # 11 domain


# ══════════════════════════════════════════════════════════════════════════
#  ① BACA NASKAH dari berkas EduAi (pola sama `belajar._bab_dari_berkas`)
# ══════════════════════════════════════════════════════════════════════════
def teks_naskah(f) -> str:
    """Ambil teks naskah dari berkas .docx milik user.

    JUJUR kalau gagal: kembalikan '' (jangan menebak).
    """
    uid = getattr(f, 'user_id', None)
    simpan = getattr(f, 'nama_simpan', None)
    if not uid or not simpan:
        return ''
    p = f'/app/uploads/{uid}/{simpan}'
    if not os.path.exists(p):
        #  jalur lokal (di luar container) — untuk uji
        p = str(Path(f'/opt/data/services/eduai-publishing/uploads/{uid}/{simpan}'))
        if not os.path.exists(p):
            return ''

    try:
        if p.lower().endswith('.docx'):
            with zipfile.ZipFile(p) as z:
                xml = z.read('word/document.xml').decode('utf-8', 'replace')
            xml = re.sub(r'</w:p>', '\n', xml)
            xml = re.sub(r'<[^>]+>', '', xml)
            return _html.unescape(xml).strip()
    except Exception:
        return ''
    return ''


def sidik(teks: str) -> str:
    """Sidik SHA-256 isi naskah — anti-giling (uji naskah SAMA dua kali)."""
    rapi = re.sub(r'\s+', ' ', teks or '').strip().lower()
    return hashlib.sha256(rapi.encode('utf-8')).hexdigest()


# ══════════════════════════════════════════════════════════════════════════
#  ② JATAH GRATIS — 1× per naskah (putusan Bos "A")
# ══════════════════════════════════════════════════════════════════════════
def _sudah_gratis(db: Session, u, fid_sidik: str) -> bool:
    """Sudah pernah uji contoh gratis untuk sidik naskah ini?

    Naskah DIUBAH ⇒ sidik berubah ⇒ otomatis dapat gratis lagi (adil).
    Kolom dipakai: `jenis` + `kata_kunci` (bukan kolom baru).
    """
    from .models import PencarianManual
    return db.query(
        db.query(PencarianManual)
          .filter(PencarianManual.user_id == u.id,
                  PencarianManual.jenis == 'gratis_mirip',
                  PencarianManual.kata_kunci == fid_sidik)
          .exists()
    ).scalar()


def _catat_gratis(db: Session, u, fid_sidik: str, keterangan: str) -> None:
    from .models import PencarianManual
    db.add(PencarianManual(user_id=u.id, jenis='gratis_mirip',
                           kata_kunci=fid_sidik,
                           hasil_jumlah=BIAYA_TOKEN))
    db.commit()


# ══════════════════════════════════════════════════════════════════════════
#  ③ UJI — satu pintu
# ══════════════════════════════════════════════════════════════════════════
def uji(db: Session, u, berkas, gratis: bool = False) -> dict:
    """Jalankan uji mirip pada satu naskah.

    Return {'pdf', 'indeks', 'jumlah_sumber', 'stabilo', 'gratis', 'dipotong'}.

    Modal (uang) dipotong DI DEPAN (sebelum mesin bekerja) — aturan Bos:
    "Jangan sampai user sudah bayar tapi tidak dapat hasil."
    """
    dari_berkas = teks_naskah(berkas)
    if not dari_berkas:
        raise HTTPException(422, detail={
            'ok': False, 'kode': 'NASKAH_KOSONG',
            'pesan': ('Naskah ini belum bisa dibaca. Pastikan berkasnya '
                      'berformat .docx dan masih ada di Naskah Saya.'),
        })

    sd = sidik(dari_berkas)
    judul = getattr(berkas, 'nama', None) or 'Naskah'

    #  ── MODE GRATIS: 1× per sidik ──
    if gratis:
        if _sudah_gratis(db, u, sd):
            raise HTTPException(409, detail={
                'ok': False, 'kode': 'SUDAH_GRATIS',
                'pesan': ('Naskah ini sudah pernah diuji contoh gratis. '
                          'Ubah sedikit isinya, atau pakai uji berbayar.'),
            })
        dipotong = 0
    else:
        #  ── MODE BERBAYAR: potong DI DEPAN (satu kantong saldo) ──
        hasil_potong = kuota.potong_banyak(db, u, BIAYA_TOKEN,
                                          jenis_addon='mirip')
        dipotong = hasil_potong.get('dipotong', 0)

    #  ── JALANKAN MESIN (pemasangan: uji_mirip → script Bos) ──
    from . import uji_mirip
    keluar = _jalur_keluar(u, berkas, sd, gratis)
    try:
        hasil = uji_mirip.buat_laporan(dari_berkas, judul, keluar, gratis=gratis)
    except Exception as e:                       # noqa: BLE001
        #  GAGAL karena mesin/trouble → KEMBALIKAN token (aturan Bos)
        if dipotong:
            from . import saldo as _saldo
            _saldo.kembalikan(db, u, dipotong, sumber='kembali',
                              catatan='uji-mirip gagal')
        raise HTTPException(500, detail={
            'ok': False, 'kode': 'MESIN_GAGAL',
            'pesan': ('Uji belum selesai karena gangguan mesin. '
                      'Tokenmu dikembalikan — coba lagi setelah beberapa saat.'),
            'asli': str(e)[:200],
        })

    if gratis:
        _catat_gratis(db, u, sd, judul)

    hasil['gratis'] = bool(gratis)
    hasil['dipotong'] = dipotong
    hasil['tidak_gratis'] = BIAYA_TOKEN
    return hasil


def _jalur_keluar(u, berkas, sd: str, gratis: bool) -> str:
    """Satu berkas keluaran per (user, naskah, mode) — di dalam uploads/."""
    uid = getattr(u, 'id', 0)
    dasar = Path(f'/app/uploads/{uid}')
    if not dasar.exists():
        dasar = Path(f'/opt/data/services/eduai-publishing/uploads/{uid}')
    dasar = dasar / 'uji-mirip'
    dasar.mkdir(parents=True, exist_ok=True)
    tanda = 'contoh' if gratis else 'hasil'
    return str(dasar / f'{tanda}-{sd[:12]}.pdf')


def ringkas(u) -> dict:
    """Keterangan untuk layar (tidak menebak saldo kalau bukan admin)."""
    return {'biaya': BIAYA_TOKEN, 'pembanding': PEMBANDING}
