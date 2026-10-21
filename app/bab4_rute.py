"""Rute HTTP BAB IV (Fase 3) — memasang fondasi app/bab4.py ke aplikasi.

Peta jalan alur (DOKUMENTASI_BAB4 §4): peta disahkan → instrumen →
data lapangan (pra/utama) → pra-survei → olah data → Kunci Hasil.
Semua rute berawalan /api/bab4 dan wajib login (pola app/ai.py).
Kepemilikan berkas selalu diperiksa: user hanya menyentuh berkasnya.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from . import bab4, jembatan_statistik, kuota
from .auth import wajib_login_api
from .models import (DataLapanganBab4, FileBerkas, PetaBab4, User,
                     get_db)

router = APIRouter(prefix='/api/bab4', tags=['bab4'],
                   dependencies=[Depends(wajib_login_api)])


def _berkas_milik(db: Session, u: User, file_id: int) -> FileBerkas:
    f = (db.query(FileBerkas)
         .filter_by(id=file_id, user_id=u.id).first())
    if f is None:
        raise HTTPException(404, 'Berkas tidak ditemukan.')
    return f


def _peta_terbaru(db: Session, u: User, file_id: int) -> PetaBab4 | None:
    return (db.query(PetaBab4)
            .filter_by(user_id=u.id, file_id=file_id)
            .order_by(PetaBab4.nomor.desc()).first())


def _peta_disahkan(db: Session, u: User, file_id: int) -> dict:
    p = _peta_terbaru(db, u, file_id)
    if p is None or p.status != 'disahkan':
        raise HTTPException(
            409, 'Peta penelitian belum disahkan. Sahkan peta dulu '
                 'sebelum langkah ini.')
    return bab4.baca_peta(p)


def _data(db: Session, u: User, file_id: int,
          tahap: str) -> DataLapanganBab4:
    d = (db.query(DataLapanganBab4)
         .filter_by(user_id=u.id, file_id=file_id, tahap=tahap).first())
    if d is None or not json.loads(d.baris or '[]'):
        raise HTTPException(
            409, f'Data tahap "{tahap}" masih kosong — isi dulu di '
                 'Halaman Data Lapangan.')
    return d


def _terjemahkan_gagal(e: Exception) -> HTTPException:
    if isinstance(e, jembatan_statistik.GagalJembatan):
        st = e.status if isinstance(e.status, int) else 502
        return HTTPException(st if 400 <= st <= 503 else 502, e.pesan)
    return HTTPException(502, f'Mesin statistik bermasalah: {e}')


# ── Ringkasan keadaan (satu panggilan untuk layar) ──────────────
@router.get('/ringkasan')
def ringkasan(file_id: int, u: User = Depends(wajib_login_api),
              db: Session = Depends(get_db)):
    _berkas_milik(db, u, file_id)
    peta = _peta_terbaru(db, u, file_id)
    terkunci = bab4.hasil_terkunci(db, u.id, file_id)
    data = {}
    for tahap in ('pra', 'utama', 'simulasi'):
        d = (db.query(DataLapanganBab4)
             .filter_by(user_id=u.id, file_id=file_id, tahap=tahap)
             .first())
        if d:
            data[tahap] = {'baris': len(json.loads(d.baris or '[]')),
                           'target': d.target_responden}
    return {
        'peta': None if peta is None else {
            'status': peta.status, 'nomor': peta.nomor},
        'data': data,
        'jumlah_generate': bab4.jumlah_generate(db, u.id, file_id),
        'tarif_generate_berikutnya':
            bab4.tarif_generate_berikutnya(db, u.id, file_id),
        'versi_terkunci': None if terkunci is None else terkunci.nomor,
    }


# ── Peta ────────────────────────────────────────────────────────
@router.post('/peta')
def simpan_peta(body: dict, u: User = Depends(wajib_login_api),
                db: Session = Depends(get_db)):
    file_id = int(body.get('file_id') or 0)
    _berkas_milik(db, u, file_id)
    peta = body.get('peta')
    if not isinstance(peta, dict):
        raise HTTPException(422, 'Isi peta harus berupa objek.')
    p = bab4.simpan_peta(db, u.id, file_id, peta)
    return {'nomor': p.nomor, 'status': p.status,
            'masalah': bab4.periksa_peta(peta)}


@router.post('/peta/sahkan')
def sahkan_peta(body: dict, u: User = Depends(wajib_login_api),
                db: Session = Depends(get_db)):
    file_id = int(body.get('file_id') or 0)
    _berkas_milik(db, u, file_id)
    p = _peta_terbaru(db, u, file_id)
    if p is None:
        raise HTTPException(404, 'Belum ada peta tersimpan.')
    masalah = bab4.periksa_peta(bab4.baca_peta(p))
    if masalah:
        raise HTTPException(422, {'pesan': 'Peta belum layak disahkan.',
                                  'masalah': masalah})
    p = bab4.sahkan_peta(db, p.id)
    return {'nomor': p.nomor, 'status': p.status}


# ── Instrumen (paket unduhan tunggal) ───────────────────────────
@router.get('/instrumen')
def instrumen(file_id: int, u: User = Depends(wajib_login_api),
              db: Session = Depends(get_db)):
    _berkas_milik(db, u, file_id)
    return bab4.buat_instrumen(_peta_disahkan(db, u, file_id))


@router.get('/instrumen/template.csv')
def unduh_template(file_id: int, u: User = Depends(wajib_login_api),
                   db: Session = Depends(get_db)):
    _berkas_milik(db, u, file_id)
    ins = bab4.buat_instrumen(_peta_disahkan(db, u, file_id))
    return PlainTextResponse(
        bab4.teks_template_csv(ins), media_type='text/csv',
        headers={'Content-Disposition':
                 'attachment; filename="template-data.csv"'})


@router.get('/instrumen/kuesioner.md')
def unduh_kuesioner(file_id: int, u: User = Depends(wajib_login_api),
                    db: Session = Depends(get_db)):
    _berkas_milik(db, u, file_id)
    ins = bab4.buat_instrumen(_peta_disahkan(db, u, file_id))
    return PlainTextResponse(
        bab4.teks_kuesioner_md(ins), media_type='text/markdown',
        headers={'Content-Disposition':
                 'attachment; filename="kuesioner.md"'})


# ── Data Lapangan ───────────────────────────────────────────────
@router.put('/data')
def simpan_data(body: dict, u: User = Depends(wajib_login_api),
                db: Session = Depends(get_db)):
    file_id = int(body.get('file_id') or 0)
    _berkas_milik(db, u, file_id)
    tahap = str(body.get('tahap') or 'utama')
    if tahap not in ('pra', 'utama', 'simulasi'):
        raise HTTPException(422, 'Tahap data tidak dikenal.')
    kolom = body.get('kolom') or []
    baris = body.get('baris') or []
    if not isinstance(kolom, list) or not isinstance(baris, list):
        raise HTTPException(422, 'Kolom dan baris harus berupa daftar.')
    d = (db.query(DataLapanganBab4)
         .filter_by(user_id=u.id, file_id=file_id, tahap=tahap).first())
    if d is None:
        d = DataLapanganBab4(user_id=u.id, file_id=file_id, tahap=tahap)
        db.add(d)
    d.kolom = json.dumps([str(k) for k in kolom])
    d.baris = json.dumps(baris)
    if body.get('target_responden') is not None:
        d.target_responden = int(body['target_responden'])
    db.commit()
    return {'tahap': tahap, 'baris': len(baris), 'kolom': len(kolom)}


@router.get('/data')
def baca_data(file_id: int, tahap: str = 'utama',
              u: User = Depends(wajib_login_api),
              db: Session = Depends(get_db)):
    _berkas_milik(db, u, file_id)
    d = (db.query(DataLapanganBab4)
         .filter_by(user_id=u.id, file_id=file_id, tahap=tahap).first())
    if d is None:
        return {'tahap': tahap, 'kolom': [], 'baris': [],
                'target_responden': None}
    return {'tahap': tahap, 'kolom': json.loads(d.kolom or '[]'),
            'baris': json.loads(d.baris or '[]'),
            'target_responden': d.target_responden}


# ── Pra-survei (uji coba instrumen; tanpa potongan token) ──────
@router.post('/pra-survei')
def pra_survei(body: dict, u: User = Depends(wajib_login_api),
               db: Session = Depends(get_db)):
    file_id = int(body.get('file_id') or 0)
    _berkas_milik(db, u, file_id)
    d = _data(db, u, file_id, 'pra')
    kolom = json.loads(d.kolom or '[]')
    payload = {'tahap': 'pra-survei',
               'baris': bab4.baris_ke_objek(
                   kolom, json.loads(d.baris or '[]')),
               'kolom': kolom}
    try:
        hasil = jembatan_statistik.hitung(payload)
    except Exception as e:  # noqa: BLE001 — diterjemahkan ke HTTP
        raise _terjemahkan_gagal(e) from e
    bab4.simpan_hasil(db, u.id, file_id, 'pra_survei', 'pra', hasil)
    return {'kartu': bab4.kartu_kesehatan(hasil), 'mentah': hasil}


# ── Olah data utama + tarif generate ────────────────────────────
@router.post('/olah-data')
def olah_data(body: dict, u: User = Depends(wajib_login_api),
              db: Session = Depends(get_db)):
    file_id = int(body.get('file_id') or 0)
    _berkas_milik(db, u, file_id)
    peta = _peta_disahkan(db, u, file_id)
    d = _data(db, u, file_id, 'utama')
    kolom = json.loads(d.kolom or '[]')
    tarif = bab4.tarif_generate_berikutnya(db, u.id, file_id)
    terpotong = 0
    if tarif > 0:
        info = kuota.potong_banyak(db, u, tarif, jenis_addon='ai')
        terpotong = int(info.get('dipotong') or 0)  # 402 bila kurang
    payload = bab4.susun_payload_hitung(peta, kolom, tahap='utama')
    payload['baris'] = bab4.baris_ke_objek(
        kolom, json.loads(d.baris or '[]'))
    try:
        hasil = jembatan_statistik.hitung(payload)
    except Exception as e:  # noqa: BLE001
        # Token TIDAK BOLEH hangus karena mesin gagal (temuan review
        # Fase 3; pola yang sama dipakai app/ai.py): kembalikan dulu,
        # baru laporkan kegagalannya.
        if terpotong:
            try:
                kuota.kembalikan_banyak(db, u, terpotong, 'ai')
            except Exception:  # noqa: BLE001 — pengembalian jangan menutupi galat asli
                pass
        raise _terjemahkan_gagal(e) from e
    # Sematkan pemetaan H1..Hn SEBELUM disimpan: narasi hanya boleh
    # membaca hasil terkunci, jadi peta hipotesis harus ikut tersimpan
    # di dalamnya (temuan review Fase 3 — BUG BARU 1).
    hasil['peta_hipotesis'] = bab4.petakan_hasil_ke_hipotesis(peta, hasil)
    h = bab4.simpan_hasil(db, u.id, file_id, 'olah_data',
                          payload['mode'], hasil)
    return {'versi': h.nomor, 'tarif_dikenakan': tarif,
            'hasil': hasil}


@router.post('/kunci-hasil')
def kunci_hasil_rute(body: dict, u: User = Depends(wajib_login_api),
                     db: Session = Depends(get_db)):
    file_id = int(body.get('file_id') or 0)
    _berkas_milik(db, u, file_id)
    h = bab4.kunci_hasil(db, u.id, file_id)
    if h is None:
        raise HTTPException(
            409, 'Tidak ada hasil baru yang lebih baru dari yang sudah '
                 'terkunci — jalankan olah data dulu.')
    return {'versi_terkunci': h.nomor}


# ── Simulasi contoh (placeholder sebelum paket aktif) ────────────
@router.get('/simulasi/contoh')
def simulasi_contoh(u: User = Depends(wajib_login_api)):
    return bab4.SIMULASI_CONTOH
