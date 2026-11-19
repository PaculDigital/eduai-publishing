"""Rute Cek Konsistensi Antar Bab (19 Nov 2026, Gas Boss).

Rancangan: RENCANA_KONSISTENSI.md.
  - POST /v1/konsistensi/mulai-latar -> titip pemeriksaan ke pekerja latar
  - GET  /v1/konsistensi/status       -> keadaan + hasil untuk polling halaman

GRATIS: tidak memotong Token Revisi. Biaya LLM dari saldo Apinex Boss
(1 panggil `_panggil_router` per pemeriksaan, pintu yang sama dengan
Jev/Hakim). Pemeriksaan jalan di pekerja latar (`proses`, pola yang
SAMA dengan /v1/peta/mulai-latar dan /v1/pustaka/mulai-latar): tekan
2x saat jalan ditahan sopan, bukan proses kedua. Gerbang sidik peta:
peta yang tidak berubah sejak pemeriksaan terakhir langsung
menampilkan hasil terakhir, tanpa panggil LLM baru. Hasil tersimpan
di Setelan (simpan_hasil). Tidak menulis apa pun ke docx mahasiswa.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from . import konsistensi as KB
from . import proses as proses_mod
from . import struktur as _str
from .auth import wajib_login_api
from .models import FileBerkas, ProfilDokumen, ProsesAI, Setelan, User, get_db

log = logging.getLogger('eduai.konsistensi.rute')

router = APIRouter()

KUNCI_HASIL = 'konsistensi_hasil_berkas_{fid}'
KOMENTAR_PROSES = 'Cek Konsistensi'
SYSTEM_KONSISTENSI = (
    'Kamu penilai skripsi yang teliti dan jujur. '
    'Jawab hanya dengan JSON.')
# Batas sabar satu panggil LLM (detik). Pemeriksaan jalan di pekerja
# latar, jadi tidak ada batas baca HTTP yang mengejar.
TIMEOUT_LLM_DETIK = 180


def simpan_hasil(db, fid: int, hasil: dict) -> None:
    """Simpan hasil cek konsistensi ke Setelan (JSON). Menimpa hasil lama."""
    kunci = KUNCI_HASIL.format(fid=int(fid))
    isi = json.dumps(hasil or {}, ensure_ascii=False)
    baris = db.get(Setelan, kunci)
    if baris is None:
        db.add(Setelan(kunci=kunci, nilai=isi, oleh='konsistensi-bab'))
    else:
        baris.nilai = isi
    db.commit()


def muat_hasil(db, fid: int) -> dict | None:
    """Muat hasil cek konsistensi. Tidak ada / rusak -> None."""
    kunci = KUNCI_HASIL.format(fid=int(fid))
    baris = db.get(Setelan, kunci)
    if baris is None or not (baris.nilai or '').strip():
        return None
    try:
        data = json.loads(baris.nilai)
    except Exception:                                          # noqa: BLE001
        return None
    return data if isinstance(data, dict) else None


def _berkas(db: Session, fid: int, uid: int) -> FileBerkas:
    fb = (db.query(FileBerkas)
            .filter(FileBerkas.id == int(fid),
                    FileBerkas.user_id == int(uid)).first())
    if fb is None:
        raise HTTPException(404, detail={'ok': False,
                                         'pesan': 'Berkas tidak ditemukan.'})
    return fb


def _adalah_proses_konsistensi(komentar_json) -> bool:
    """True bila proses ini pemeriksaan konsistensi (bukan peta/pustaka)."""
    try:
        isi = json.loads(komentar_json or '[]')
    except Exception:                                          # noqa: BLE001
        isi = []
    if isinstance(isi, list):
        return KOMENTAR_PROSES in [str(x) for x in isi]
    return KOMENTAR_PROSES in str(isi)


def _pemeriksaan_terkini(db: Session, user_id: int, file_id: int,
                         hasil_ada: bool) -> dict:
    """Keadaan pemeriksaan konsistensi (pola pustaka_status)."""
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
        if not _adalah_proses_konsistensi(
                getattr(p, 'komentar_json', '') or ''):
            continue
        d = {'kode': p.kode, 'status': p.status, 'galat': p.galat or ''}
        if terakhir is None:
            terakhir = d
        if p.status in ('menunggu', 'jalan') and jalan is None:
            jalan = d
    return _str.keadaan_pemeriksaan(
        proses_jalan=jalan, proses_terakhir=terakhir, peta_ada=hasil_ada)


@router.get('/v1/konsistensi/status')
async def konsistensi_status(file_id: int,
                             u: User = Depends(wajib_login_api),
                             db: Session = Depends(get_db)):
    """Keadaan cek konsistensi untuk polling halaman (ringan)."""
    fb = _berkas(db, file_id, u.id)
    hasil = muat_hasil(db, file_id)
    keadaan = _pemeriksaan_terkini(db, u.id, file_id, hasil is not None)
    prof = (db.query(ProfilDokumen)
              .filter(ProfilDokumen.file_id == int(file_id),
                      ProfilDokumen.user_id == u.id).first())
    peta_ada = bool(prof and (prof.peta_json or '').strip())
    return {'ok': True, 'file_id': int(file_id),
            'keadaan': keadaan.get('keadaan', 'belum'),
            'galat': keadaan.get('galat', ''),
            'peta_ada': peta_ada,
            'vonis': (hasil or {}).get('vonis'),
            'langkah_berikut': (hasil or {}).get('langkah_berikut'),
            'diperiksa_pada': (hasil or {}).get('diperiksa_pada')}


@router.post('/v1/konsistensi/mulai-latar')
async def konsistensi_mulai_latar(
    request: Request,
    u: User = Depends(wajib_login_api),
    db: Session = Depends(get_db),
):
    """TITIP cek konsistensi lalu BALAS CEPAT.

    Pola yang SAMA dengan /v1/pustaka/mulai-latar: endpoint ini HANYA
    menitipkan pekerjaan ke pekerja latar (`proses`) lalu langsung
    membalas; halaman membaca keadaan lewat `konsistensi_status`
    sampai selesai. Tekan 2x saat jalan: yang kedua DITAHAN sopan
    (dijadwalkan False, sedang_jalan True), bukan proses kedua.
    Peta yang tidak berubah sejak pemeriksaan terakhir: hasil terakhir
    langsung dikembalikan (sudah_tersedia), tanpa panggil LLM baru.
    Tanpa peta (belum Periksa Struktur): ditolak, karena 6 pernyataan
    diekstrak dari peta Jev.
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
                 and _adalah_proses_konsistensi(
                     getattr(p, 'komentar_json', '') or '')]
    except Exception as e:                                  # noqa: BLE001
        log.warning('[konsistensi] cek proses berjalan gagal: %s', e)
    if jalan:
        return {'ok': True, 'dijadwalkan': False, 'sedang_jalan': True,
                'kode': jalan[0].kode,
                'alasan': 'masih ada pemeriksaan berjalan untuk naskah ini'}
    prof = (db.query(ProfilDokumen)
              .filter(ProfilDokumen.file_id == fid,
                      ProfilDokumen.user_id == u.id).first())
    if not prof or not (prof.peta_json or '').strip():
        return {'ok': False, 'dijadwalkan': False, 'sedang_jalan': False,
                'alasan': 'Periksa Struktur dulu, supaya naskah bisa dibaca.'}
    lama = muat_hasil(db, fid)
    if lama and (lama.get('peta_sidik') or '') \
            and lama.get('peta_sidik') == (prof.peta_sidik or ''):
        return {'ok': True, 'dijadwalkan': False, 'sedang_jalan': False,
                'sudah_tersedia': True,
                'diperiksa_pada': lama.get('diperiksa_pada'),
                'alasan': 'Naskah tidak berubah sejak pemeriksaan terakhir. '
                          'Menampilkan hasil terakhir.'}
    p = proses_mod.mulai(db, user_id=u.id, file_id=fid,
                         komentar=[KOMENTAR_PROSES])

    async def _kerja(lapor):
        d2 = proses_mod._sesi_baru()
        try:
            from .ai import _panggil_router
            prof2 = (d2.query(ProfilDokumen)
                       .filter(ProfilDokumen.file_id == fid,
                               ProfilDokumen.user_id == u.id).first())
            if not prof2 or not (prof2.peta_json or '').strip():
                raise RuntimeError(
                    'Periksa Struktur dulu, supaya naskah bisa dibaca.')
            bagian = KB.ekstrak_bagian_bab(prof2.peta_json)
            if not any((v or '').strip() for v in bagian.values()):
                raise RuntimeError(
                    'Enam bagian (masalah, tujuan, hipotesis, metode, '
                    'hasil, kesimpulan) tidak ditemukan di naskah.')
            prompt = KB.susun_prompt_bab(bagian)
            teks_jawaban, _info = await _panggil_router(
                prompt, timeout=TIMEOUT_LLM_DETIK,
                system=SYSTEM_KONSISTENSI)
            vonis = KB.urai_jawaban_bab(teks_jawaban or '')
            hasil = {
                'peta_sidik': prof2.peta_sidik or '',
                'diperiksa_pada': datetime.now(timezone.utc).isoformat(),
                'vonis': vonis,
                'langkah_berikut': KB.langkah_berikut_bab(vonis),
            }
            simpan_hasil(d2, fid, hasil)
            proses_mod.tandai_selesai(
                p.kode, hasil='Cek Konsistensi selesai.')
        except Exception as e:                              # noqa: BLE001
            log.error('[konsistensi] pemeriksaan %s gagal: %s', p.kode, e)
            proses_mod.tandai_gagal(p.kode, str(e)[:300])
        finally:
            d2.close()

    proses_mod.jalankan(p.kode, _kerja)
    return {'ok': True, 'dijadwalkan': True, 'kode': p.kode}
