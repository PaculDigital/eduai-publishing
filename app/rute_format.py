"""Rute Cek Format Pedoman (19 Nov 2026, Gas Boss).

Rancangan: RENCANA_FORMAT.md. Logika di app/standar_penulisan.py Bagian 2
(melengkapi modul yang sudah ada, bukan modul baru).
  - POST /v1/format/mulai-latar -> titip pemeriksaan ke pekerja latar
  - GET  /v1/format/status       -> keadaan + hasil untuk polling halaman

GRATIS: deterministik, TANPA LLM, 0 token. Pemeriksaan jalan di pekerja
latar (`proses`, pola yang SAMA dengan /v1/konsistensi/mulai-latar dan
/v1/pustaka/mulai-latar): tekan 2x saat jalan ditahan sopan, bukan proses
kedua. Gerbang sidik berkas (SHA-256 .docx, pola pustaka_periksa.sidik_berkas):
berkas yang tidak berubah sejak pemeriksaan terakhir langsung menampilkan
hasil terakhir, tanpa baca ulang. Hasil tersimpan di Setelan (simpan_hasil).
Tidak menulis apa pun ke docx mahasiswa. Tidak butuh Periksa Struktur dulu
(pemeriksa membaca .docx langsung, bukan peta).
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from . import proses as proses_mod
from . import standar_penulisan as SP
from . import struktur as _str
from .auth import wajib_login_api
from .config import UPLOAD_DIR
from .models import FileBerkas, ProsesAI, Setelan, User, get_db

log = logging.getLogger('eduai.format.rute')

router = APIRouter()

KUNCI_HASIL = 'format_hasil_berkas_{fid}'
KOMENTAR_PROSES = 'Cek Format'


def simpan_hasil(db, fid: int, hasil: dict) -> None:
    """Simpan hasil cek format ke Setelan (JSON). Menimpa hasil lama."""
    kunci = KUNCI_HASIL.format(fid=int(fid))
    isi = json.dumps(hasil or {}, ensure_ascii=False)
    baris = db.get(Setelan, kunci)
    if baris is None:
        db.add(Setelan(kunci=kunci, nilai=isi, oleh='cek-format'))
    else:
        baris.nilai = isi
    db.commit()


def muat_hasil(db, fid: int) -> dict | None:
    """Muat hasil cek format. Tidak ada / rusak -> None."""
    kunci = KUNCI_HASIL.format(fid=int(fid))
    baris = db.get(Setelan, kunci)
    if baris is None or not (baris.nilai or '').strip():
        return None
    try:
        data = json.loads(baris.nilai)
    except Exception:                                          # noqa: BLE001
        return None
    return data if isinstance(data, dict) else None


def jalur_docx(fb: FileBerkas) -> Path:
    """Lokasi .docx di disk: UPLOAD_DIR/<user_id>/<nama_simpan>."""
    return UPLOAD_DIR / str(fb.user_id) / fb.nama_simpan


def sidik_berkas(jalur: Path) -> str | None:
    """SHA-256 berkas (pola pustaka_periksa.sidik_berkas)."""
    try:
        with open(jalur, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:                                          # noqa: BLE001
        return None


def _berkas(db: Session, fid: int, uid: int) -> FileBerkas:
    fb = (db.query(FileBerkas)
            .filter(FileBerkas.id == int(fid),
                    FileBerkas.user_id == int(uid)).first())
    if fb is None:
        raise HTTPException(404, detail={'ok': False,
                                         'pesan': 'Berkas tidak ditemukan.'})
    return fb


def _adalah_proses_format(komentar_json) -> bool:
    """True bila proses ini pemeriksaan format (bukan peta/pustaka/konsistensi)."""
    try:
        isi = json.loads(komentar_json or '[]')
    except Exception:                                          # noqa: BLE001
        isi = []
    if isinstance(isi, list):
        return KOMENTAR_PROSES in [str(x) for x in isi]
    return KOMENTAR_PROSES in str(isi)


def _pemeriksaan_terkini(db: Session, user_id: int, file_id: int,
                         hasil_ada: bool) -> dict:
    """Keadaan pemeriksaan format (pola pustaka_status)."""
    try:
        semua = (db.query(ProsesAI)
                   .filter(ProsesAI.user_id == int(user_id),
                           ProsesAI.file_id == int(file_id))
                   .order_by(ProsesAI.id.desc()).limit(20).all())
    except Exception:                                          # noqa: BLE001
        return _str.keadaan_pemeriksaan(
            proses_jalan=None, proses_terakhir=None, peta_ada=hasil_ada)
    jalan = None
    terakhir = None
    for p in semua:
        if not _adalah_proses_format(
                getattr(p, 'komentar_json', '') or ''):
            continue
        d = {'kode': p.kode, 'status': p.status, 'galat': p.galat or ''}
        if terakhir is None:
            terakhir = d
        if p.status in ('menunggu', 'jalan') and jalan is None:
            jalan = d
    return _str.keadaan_pemeriksaan(
        proses_jalan=jalan, proses_terakhir=terakhir, peta_ada=hasil_ada)


@router.get('/v1/format/status')
async def format_status(file_id: int,
                        u: User = Depends(wajib_login_api),
                        db: Session = Depends(get_db)):
    """Keadaan cek format untuk polling halaman (ringan)."""
    fb = _berkas(db, file_id, u.id)
    hasil = muat_hasil(db, file_id)
    keadaan = _pemeriksaan_terkini(db, u.id, file_id, hasil is not None)
    return {'ok': True, 'file_id': int(file_id),
            'keadaan': keadaan.get('keadaan', 'belum'),
            'galat': keadaan.get('galat', ''),
            'ringkasan': (hasil or {}).get('ringkasan'),
            'temuan': (hasil or {}).get('temuan'),
            'langkah_berikut': (hasil or {}).get('langkah_berikut'),
            'diperiksa_pada': (hasil or {}).get('diperiksa_pada')}


@router.post('/v1/format/mulai-latar')
async def format_mulai_latar(
    request: Request,
    u: User = Depends(wajib_login_api),
    db: Session = Depends(get_db),
):
    """TITIP cek format lalu BALAS CEPAT.

    Pola yang SAMA dengan /v1/konsistensi/mulai-latar: endpoint ini HANYA
    menitipkan pekerjaan ke pekerja latar (`proses`) lalu langsung
    membalas; halaman membaca keadaan lewat `format_status` sampai selesai.
    Tekan 2x saat jalan: yang kedua DITAHAN sopan (dijadwalkan False,
    sedang_jalan True), bukan proses kedua. Berkas yang tidak berubah sejak
    pemeriksaan terakhir: hasil terakhir langsung dikembalikan
    (sudah_tersedia), tanpa baca ulang.
    """
    body = await request.json()
    if not isinstance(body, dict):
        body = {}
    try:
        fid = int(body.get('file_id') or 0)
    except (TypeError, ValueError):
        raise HTTPException(400, detail={'ok': False,
                                         'pesan': '`file_id` harus angka.'})
    fb = _berkas(db, fid, u.id)
    jalan = []
    try:
        semua = proses_mod.yang_sedang_jalan(db, u.id)
        jalan = [p for p in semua if p.file_id == fid
                 and _adalah_proses_format(
                     getattr(p, 'komentar_json', '') or '')]
    except Exception as e:                                  # noqa: BLE001
        log.warning('[format] cek proses berjalan gagal: %s', e)
    if jalan:
        return {'ok': True, 'dijadwalkan': False, 'sedang_jalan': True,
                'kode': jalan[0].kode,
                'alasan': 'masih ada pemeriksaan berjalan untuk naskah ini'}
    jalur = jalur_docx(fb)
    if not jalur.is_file():
        return {'ok': False, 'dijadwalkan': False, 'sedang_jalan': False,
                'alasan': 'Berkas .docx tidak ditemukan di server.'}
    sidik = sidik_berkas(jalur)
    lama = muat_hasil(db, fid)
    if lama and sidik and (lama.get('sidik_berkas') or '') == sidik:
        return {'ok': True, 'dijadwalkan': False, 'sedang_jalan': False,
                'sudah_tersedia': True,
                'diperiksa_pada': lama.get('diperiksa_pada'),
                'alasan': 'Berkas tidak berubah sejak pemeriksaan terakhir. '
                          'Menampilkan hasil terakhir.'}
    p = proses_mod.mulai(db, user_id=u.id, file_id=fid,
                         komentar=[KOMENTAR_PROSES])

    async def _kerja(lapor):
        d2 = proses_mod._sesi_baru()
        try:
            fb2 = (d2.query(FileBerkas)
                     .filter(FileBerkas.id == int(fid),
                             FileBerkas.user_id == u.id).first())
            if fb2 is None:
                raise RuntimeError('Berkas tidak ditemukan.')
            jalur2 = jalur_docx(fb2)
            if not jalur2.is_file():
                raise RuntimeError('Berkas .docx tidak ditemukan di server.')
            hasil = SP.periksa_format(jalur2)
            simpan_hasil(d2, fid, hasil)
            proses_mod.tandai_selesai(
                p.kode, hasil='Cek Format selesai.')
        except Exception as e:                              # noqa: BLE001
            log.error('[format] pemeriksaan %s gagal: %s', p.kode, e)
            proses_mod.tandai_gagal(p.kode, str(e)[:300])
        finally:
            d2.close()

    proses_mod.jalankan(p.kode, _kerja)
    return {'ok': True, 'dijadwalkan': True, 'kode': p.kode}
