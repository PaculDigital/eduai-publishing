"""Rute HTTP BAB IV (Fase 3) — memasang fondasi app/bab4.py ke aplikasi.

Peta jalan alur (DOKUMENTASI_BAB4 §4): peta disahkan → instrumen →
data lapangan (pra/utama) → pra-survei → olah data → Kunci Hasil.
Semua rute berawalan /api/bab4 dan wajib login (pola app/ai.py).
Kepemilikan berkas selalu diperiksa: user hanya menyentuh berkasnya.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from . import bab4, jembatan_statistik, kuota
from .auth import wajib_login_api
from .models import (DataLapanganBab4, FileBerkas, PetaBab4, User,
                     get_db)

router = APIRouter(prefix='/api/bab4', tags=['bab4'],
                   dependencies=[Depends(wajib_login_api)])

# ── Layar HTML (Fase 3 sisa): satu halaman per berkas ────────────
from pathlib import Path as _Path

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates as _Jinja

from .auth import wajib_login as _wajib_login_html

_templates = _Jinja(directory=str(_Path(__file__).parent / 'templates'))
router_layar = APIRouter(tags=['bab4-layar'])


@router_layar.get('/bab4/{file_id}', response_class=HTMLResponse)
def layar_bab4(file_id: int, request: Request,
               u: User = Depends(_wajib_login_html),
               db: Session = Depends(get_db)):
    f = _berkas_milik(db, u, file_id)
    return _templates.TemplateResponse(
        'bab4.html', {'request': request, 'file_id': file_id,
                      'nama_berkas': f.nama})


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
    kolom = [str(k) for k in kolom]
    # Normalisasi & validasi di PINTU MASUK (temuan review ronde 5):
    # baris boleh daftar (urutan kolom) atau objek {kolom: nilai}
    # (bentuk wajar dari layar) — keduanya disimpan sebagai daftar.
    # Sel hanya boleh angka atau kosong; teks seperti "abc" ditolak
    # 422 dengan posisi persisnya, BUKAN disimpan lalu berbeda hasil.
    baris_bersih: list[list] = []
    for no, b in enumerate(baris, start=1):
        if isinstance(b, dict):
            b = [b.get(k) for k in kolom]
        if not isinstance(b, list):
            raise HTTPException(
                422, f'Baris ke-{no} bentuknya tidak dikenal — kirim '
                     'daftar angka atau objek kolom.')
        sel_bersih = []
        for j, sel in enumerate(b):
            if sel is None or sel == '':
                sel_bersih.append(None)
                continue
            if isinstance(sel, bool):
                raise HTTPException(
                    422, f'Baris ke-{no}, kolom {kolom[j] if j < len(kolom) else j}: '
                         'isinya harus angka (1–5) atau kosong.')
            if isinstance(sel, (int, float)):
                sel_bersih.append(sel)
                continue
            try:
                sel_bersih.append(float(str(sel).replace(',', '.')))
            except (TypeError, ValueError):
                raise HTTPException(
                    422, f'Baris ke-{no}, kolom '
                         f'{kolom[j] if j < len(kolom) else j}: isinya '
                         f'"{sel}" — harus angka (1–5) atau kosong.') from None
        baris_bersih.append(sel_bersih)
    baris = baris_bersih
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
    tahap_data = str(body.get('tahap') or 'utama')
    if tahap_data not in ('utama', 'simulasi'):
        raise HTTPException(422, 'Tahap olah data hanya utama/simulasi.')
    d = _data(db, u, file_id, tahap_data)
    kolom = json.loads(d.kolom or '[]')
    # Simulasi = latihan dari paket: tarif selalu 0 dan hasilnya
    # disimpan berjenis 'simulasi' — TIDAK menggerus jatah generate
    # data asli dan TIDAK bisa dikunci sebagai hasil penelitian.
    tarif = (0 if tahap_data == 'simulasi' else
             bab4.tarif_generate_berikutnya(db, u.id, file_id))
    terpotong = 0
    if tarif > 0:
        info = kuota.potong_banyak(db, u, tarif, jenis_addon='ai')
        terpotong = int(info.get('dipotong') or 0)  # 402 bila kurang
    try:
        payload = bab4.susun_payload_hitung(peta, kolom, tahap='utama')
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
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
    jenis_hasil = 'simulasi' if tahap_data == 'simulasi' else 'olah_data'
    h = bab4.simpan_hasil(db, u.id, file_id, jenis_hasil,
                          payload['mode'], hasil)
    return {'versi': h.nomor, 'jenis': jenis_hasil,
            'tarif_dikenakan': tarif, 'hasil': hasil}


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


# ── Baca hasil (GLOBAL 1: hasil WAJIB bisa dibaca kembali) ─────
@router.get('/hasil')
def baca_hasil_rute(file_id: int, jenis: str = 'olah_data',
                    versi: int | None = None,
                    u: User = Depends(wajib_login_api),
                    db: Session = Depends(get_db)):
    """Daftar versi hasil + isi. Tanpa `versi`: kembalikan metadata
    semua versi dan isi versi TERKUNCI (bahan narasi BAB IV). Dengan
    `versi`: isi versi itu. Jenis: olah_data | pra_survei | simulasi."""
    from .models import HasilBab4
    _berkas_milik(db, u, file_id)
    if jenis not in ('olah_data', 'pra_survei', 'simulasi', 'narasi'):
        raise HTTPException(422, 'Jenis hasil tidak dikenal.')
    semua = (db.query(HasilBab4)
             .filter_by(user_id=u.id, file_id=file_id, jenis=jenis)
             .order_by(HasilBab4.nomor).all())
    meta = [{'nomor': h.nomor, 'status': h.status, 'mode': h.mode,
             'dibuat': h.dibuat.isoformat() if h.dibuat else None,
             'dikunci_pada': (h.dikunci_pada.isoformat()
                              if h.dikunci_pada else None)}
            for h in semua]
    if versi is not None:
        pilih = next((h for h in semua if h.nomor == versi), None)
        if pilih is None:
            raise HTTPException(404, 'Versi hasil tidak ditemukan.')
        return {'meta': meta, 'isi': bab4.baca_hasil(pilih),
                'nomor': pilih.nomor, 'status': pilih.status}
    terkunci = bab4.hasil_terkunci(db, u.id, file_id, jenis)
    return {'meta': meta,
            'terkunci': None if terkunci is None else {
                'nomor': terkunci.nomor,
                'isi': bab4.baca_hasil(terkunci)}}


# ── Profil responden 4.1 (GLOBAL 3: fungsi deskriptif disambung) ─
@router.get('/profil')
def profil(file_id: int, kolom_frekuensi: str = '',
           u: User = Depends(wajib_login_api),
           db: Session = Depends(get_db)):
    """Bahan BAB IV 4.1 dari data utama: jumlah masuk, target,
    tingkat pengembalian, dan frekuensi kolom identitas yang diminta
    (?kolom_frekuensi=Jenis_Kelamin,Usia). Dihitung di EduAi sendiri
    (deskriptif ringan, bukan uji statistik)."""
    _berkas_milik(db, u, file_id)
    d = (db.query(DataLapanganBab4)
         .filter_by(user_id=u.id, file_id=file_id, tahap='utama').first())
    if d is None:
        return {'responden_masuk': 0, 'target': None,
                'tingkat_pengembalian_persen': None, 'frekuensi': {}}
    kolom = json.loads(d.kolom or '[]')
    baris = json.loads(d.baris or '[]')
    frek = {}
    for nama in [x.strip() for x in kolom_frekuensi.split(',') if x.strip()]:
        frek[nama] = bab4.frekuensi_kolom(baris, kolom, nama)
    return {'responden_masuk': len(baris), 'target': d.target_responden,
            'tingkat_pengembalian_persen':
                bab4.tingkat_pengembalian(len(baris), d.target_responden),
            'frekuensi': frek}


# ── Simulasi sungguhan (bonus paket olah data) ──────────────────
@router.post('/simulasi/buat')
def simulasi_buat(body: dict, u: User = Depends(wajib_login_api),
                  db: Session = Depends(get_db)):
    """Buat data latihan dari model user sendiri via mesin BUAT
    DATA, simpan sebagai data tahap 'simulasi'. Tanpa potongan token
    (bonus paket, keputusan harga final 21 Okt)."""
    file_id = int(body.get('file_id') or 0)
    _berkas_milik(db, u, file_id)
    peta = _peta_disahkan(db, u, file_id)
    try:
        minta = bab4.susun_permintaan_simulasi(
            peta, n=int(body.get('n') or 120), efek=body.get('efek') or {})
    except (ValueError, TypeError) as e:
        raise HTTPException(422, str(e)) from e
    try:
        hasil = jembatan_statistik.buat_data_simulasi(minta)
    except Exception as e:  # noqa: BLE001
        raise _terjemahkan_gagal(e) from e
    d = (db.query(DataLapanganBab4)
         .filter_by(user_id=u.id, file_id=file_id, tahap='simulasi').first())
    if d is None:
        d = DataLapanganBab4(user_id=u.id, file_id=file_id, tahap='simulasi')
        db.add(d)
    d.kolom = json.dumps(hasil.get('kolom') or [])
    d.baris = json.dumps(hasil.get('baris') or [])
    db.commit()
    return {'kolom': hasil.get('kolom'), 'jumlah_baris': len(hasil.get('baris') or []),
            'laporan': hasil.get('laporan')}


@router.get('/data/unduh.csv')
def unduh_data_csv(file_id: int, tahap: str = 'simulasi',
                   u: User = Depends(wajib_login_api),
                   db: Session = Depends(get_db)):
    """Unduh data tersimpan (format template resmi: kepala kolom +
    satu baris per responden) — untuk simulasi: berkas latihan yang
    bisa diunggah balik / dibawa ke SPSS/SmartPLS."""
    _berkas_milik(db, u, file_id)
    d = _data(db, u, file_id, tahap)
    kolom = json.loads(d.kolom or '[]')
    baris = json.loads(d.baris or '[]')
    teks = [','.join(kolom)]
    for b in baris:
        teks.append(','.join('' if s is None else str(s) for s in b))
    return PlainTextResponse(
        '\n'.join(teks) + '\n', media_type='text/csv',
        headers={'Content-Disposition':
                 f'attachment; filename="data-{tahap}.csv"'})


# ── Narasi dari hasil terkunci ──────────────────────────────────
@router.post('/narasi')
async def buat_narasi(body: dict, u: User = Depends(wajib_login_api),
                      db: Session = Depends(get_db)):
    """Hasilkan narasi BAB IV dari hasil TERKUNCI saja.

    Tarif (keputusan harga final): narasi pertama 30 token; buat
    ulang berikutnya 5 token (mengikuti pola generate ulang yang
    sudah ada); suntingan manual lewat PUT /narasi/teks gratis.
    Token dipotong SESUDAH draf berhasil dibuat — gagal buat, tidak
    ada potongan."""
    from . import bab4_narasi
    file_id = int(body.get('file_id') or 0)
    _berkas_milik(db, u, file_id)
    bahan = bab4_narasi.kumpulkan_bahan(db, u, file_id)
    if bahan is None:
        raise HTTPException(
            409, 'Belum ada hasil yang dikunci. Kunci hasil dulu — '
                 'narasi hanya lahir dari angka yang sudah dikunci.')
    draf = bab4_narasi.susun_draf(bahan)
    teks, dipoles = await bab4_narasi.poles_ai(draf)
    sudah_ada = (db.query(bab4.HasilBab4)
                 .filter_by(user_id=u.id, file_id=file_id, jenis='narasi')
                 .count() > 0)
    tarif = 5 if sudah_ada else 30
    terpotong = 0
    if tarif > 0:
        info = kuota.potong_banyak(db, u, tarif, jenis_addon='ai')
        terpotong = int(info.get('dipotong') or 0)
    h = bab4.simpan_hasil(
        db, u.id, file_id, 'narasi', bahan['mode'],
        {'teks': teks, 'dari_versi_terkunci': bahan['versi_terkunci'],
         'dipoles_ai': dipoles})
    return {'versi': h.nomor, 'tarif_dikenakan': terpotong,
            'dipoles_ai': dipoles, 'teks': teks}


@router.put('/narasi/teks')
def sunting_narasi(body: dict, u: User = Depends(wajib_login_api),
                   db: Session = Depends(get_db)):
    """Suntingan manual narasi — gratis (aturan revisi lama),
    tersimpan sebagai versi narasi baru."""
    file_id = int(body.get('file_id') or 0)
    _berkas_milik(db, u, file_id)
    teks = str(body.get('teks') or '')
    if not teks.strip():
        raise HTTPException(422, 'Teks narasi kosong.')
    terkunci = bab4.hasil_terkunci(db, u.id, file_id, 'olah_data')
    h = bab4.simpan_hasil(
        db, u.id, file_id, 'narasi',
        terkunci.mode if terkunci else '',
        {'teks': teks, 'suntingan_manual': True,
         'dari_versi_terkunci': terkunci.nomor if terkunci else None})
    return {'versi': h.nomor, 'tarif_dikenakan': 0}
