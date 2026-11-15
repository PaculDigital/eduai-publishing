#!/usr/bin/env python3
"""Uji pemeriksaan struktur DI LATAR (15 Nov 2026, perintah Bos 11:12).

Jalankan `python3 tests/test_peta_latar.py`, keluar 0 bila semua lulus.
Memakai model asli + DB sqlite sementara lewat EDUAI_DATA_DIR, DB
produksi tidak tersentuh. `peta_mulai` ASLI tidak dipanggil, diganti
palsu yang lambat (tidur 2 detik) supaya terbukti tombol membalas cepat
sementara pemeriksaan tetap jalan sampai selesai.

Yang diuji:
  1. `struktur.adalah_proses_peta`: manual + otomatis cocok, revisi tidak.
  2. `struktur.keadaan_pemeriksaan`: transisi jalan > gagal > selesai >
     belum; upaya terakhir yang berhasil menutupi kegagalan lama.
  3. Endpoint `peta_mulai_latar`: tekan membalas CEPAT (< 1,5 detik)
     walau kerja palsu tidur 2 detik; pekerja menandai selesai; keadaan
     status jalan -> selesai (peta tersimpan).
  4. Tekan 2x saat jalan: yang kedua DITAHAN sopan (dijadwalkan False,
     sedang_jalan True), hanya 1 baris proses.
  5. Gagal jujur: pekerja yang melempar HTTPException menyimpan pesan
     ramah ('Naskah tidak bisa dibaca.'); galat umum memakai kalimat
     baku; keadaan status 'gagal'.
"""
import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_latar_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
# Kunci palsu untuk uji saja (DB sementara, bukan produksi).
os.environ.setdefault('EDUAI_SECRET_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_ROUTER_KEY', 'uji-sementara-bukan-rahasia')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, '/tmp/j2check')  # sqlalchemy (di venv app sudah ada)

LULUS = []
GAGAL = []


def cek(nama, benar, info=''):
    (LULUS if benar else GAGAL).append(nama)
    print(('  LULUS  ' if benar else '  GAGAL  ') + nama
          + (f'  [{info}]' if info and not benar else ''))


class _ReqPalsu:
    """Peniru Request: hanya .json() yang dipakai endpoint latar."""

    def __init__(self, body):
        self._body = dict(body or {})

    async def json(self):
        return self._body


def _tunggu_status(kode, status, batas=15.0):
    """Polling sesi baru sampai baris proses mencapai status (atau habis)."""
    from app.models import ProsesAI, SessionLocal
    t0 = time.time()
    while time.time() - t0 < batas:
        db = SessionLocal()
        try:
            p = db.query(ProsesAI).filter(ProsesAI.kode == kode).first()
            if p is not None and p.status == status:
                return True
        finally:
            db.close()
        time.sleep(0.2)
    return False


def main():
    from fastapi import HTTPException

    from app import ai as ai_mod
    from app import struktur as st
    from app.models import (FileBerkas, ProfilDokumen, ProsesAI,
                            SessionLocal, User, init_db)

    # ── 1. penanda proses peta (murni) ──────────────────────────────
    cek('latar: komentar manual cocok',
        st.adalah_proses_peta(json.dumps(['Pemeriksaan struktur'])))
    cek('latar: komentar otomatis cocok',
        st.adalah_proses_peta(
            json.dumps(['Pemeriksaan struktur otomatis'])))
    cek('latar: komentar revisi TIDAK cocok',
        not st.adalah_proses_peta(json.dumps(['Revisi Bab II'])))
    cek('latar: daftar kosong TIDAK cocok',
        not st.adalah_proses_peta(json.dumps([])))
    cek('latar: teks sampah TIDAK cocok',
        not st.adalah_proses_peta('bukan json {['))
    cek('latar: komentar kosong TIDAK cocok',
        not st.adalah_proses_peta(''))

    # ── 2. mesin keadaan (murni) ────────────────────────────────────
    jalan = {'kode': 'k1', 'status': 'jalan', 'galat': ''}
    gagal = {'kode': 'k2', 'status': 'gagal',
             'galat': 'Naskah tidak bisa dibaca.'}
    selesai = {'kode': 'k3', 'status': 'selesai', 'galat': ''}
    cek('latar: jalan mengalahkan gagal + peta',
        st.keadaan_pemeriksaan(
            proses_jalan=jalan, proses_terakhir=gagal,
            peta_ada=True)['keadaan'] == 'jalan')
    cek('latar: gagal terbaru -> gagal + pesan terbawa',
        st.keadaan_pemeriksaan(
            proses_jalan=None, proses_terakhir=gagal,
            peta_ada=True) == {'keadaan': 'gagal', 'kode': 'k2',
                               'galat': 'Naskah tidak bisa dibaca.'})
    cek('latar: gagal tanpa peta -> gagal',
        st.keadaan_pemeriksaan(
            proses_jalan=None, proses_terakhir=gagal,
            peta_ada=False)['keadaan'] == 'gagal')
    cek('latar: upaya terakhir berhasil menutupi gagal lama',
        st.keadaan_pemeriksaan(
            proses_jalan=None, proses_terakhir=selesai,
            peta_ada=True)['keadaan'] == 'selesai')
    cek('latar: tanpa proses + peta ada -> selesai',
        st.keadaan_pemeriksaan(
            proses_jalan=None, proses_terakhir=None,
            peta_ada=True)['keadaan'] == 'selesai')
    cek('latar: tanpa proses + tanpa peta -> belum',
        st.keadaan_pemeriksaan(
            proses_jalan=None, proses_terakhir=None,
            peta_ada=False)['keadaan'] == 'belum')

    # ── 3-5. endpoint + pekerja (DB sementara) ──────────────────────
    init_db()
    db = SessionLocal()
    u = User(email='uji@contoh.id', password_hash='x', nama='Asih')
    db.add(u)
    db.commit()
    fb = FileBerkas(user_id=u.id, nama='SKRIPSI-Asih.docx',
                    nama_simpan='skripsi.docx', ukuran=1000)
    db.add(fb)
    db.commit()
    uid, fid = u.id, fb.id

    asli_peta_mulai = ai_mod.peta_mulai

    async def _palsu_lambat(request, uu, d2):
        """Palsu peta_mulai: tidur 2 detik lalu SIMPAN peta (seperti asli)."""
        await asyncio.sleep(2.0)
        body = await request.json()
        prof = (d2.query(ProfilDokumen)
                  .filter(ProfilDokumen.file_id == int(body['file_id']),
                          ProfilDokumen.user_id == uu.id).first())
        if prof is None:
            prof = ProfilDokumen(file_id=int(body['file_id']),
                                 user_id=uu.id, sumber='unggah')
            d2.add(prof)
        prof.peta_json = json.dumps({'ok': True}, ensure_ascii=False)
        prof.peta_sidik = 'sidik-palsu'
        d2.commit()
        return {'ok': True}

    ai_mod.peta_mulai = _palsu_lambat
    try:
        t0 = time.time()
        hasil = asyncio.run(ai_mod.peta_mulai_latar(
            _ReqPalsu({'file_id': fid}), u, db))
        elap = time.time() - t0
    finally:
        pass
    cek('latar: tekan membalas cepat (< 1,5 detik) walau kerja 2 detik',
        hasil.get('ok') and hasil.get('dijadwalkan') and elap < 1.5,
        f'{elap:.2f} detik')
    kode = hasil.get('kode')

    # Saat pekerja masih tidur, keadaan harus 'jalan' (dibaca dari server).
    db.expire_all()
    cek('latar: saat jalan, status melaporkan jalan',
        ai_mod._pemeriksaan_terkini(
            db, uid, fid, peta_ada=False)['keadaan'] == 'jalan')

    # Tekan 2x saat jalan: ditahan sopan, tidak ada proses kedua.
    hasil2 = asyncio.run(ai_mod.peta_mulai_latar(
        _ReqPalsu({'file_id': fid}), u, db))
    cek('latar: tekan 2x saat jalan ditahan (dijadwalkan False)',
        hasil2.get('ok') and not hasil2.get('dijadwalkan')
        and hasil2.get('sedang_jalan') is True)
    db2 = SessionLocal()
    n_proses = db2.query(ProsesAI).filter(
        ProsesAI.user_id == uid, ProsesAI.file_id == fid).count()
    db2.close()
    cek('latar: tekan 2x hanya membuat 1 baris proses',
        n_proses == 1, f'{n_proses} baris')

    cek('latar: pekerja selesai (status selesai)',
        _tunggu_status(kode, 'selesai'))
    db.expire_all()
    cek('latar: sesudah selesai + peta tersimpan -> keadaan selesai',
        ai_mod._pemeriksaan_terkini(
            db, uid, fid, peta_ada=True)['keadaan'] == 'selesai')

    # ── 5. gagal jujur ──────────────────────────────────────────────
    async def _palsu_gagal_http(request, uu, d2):
        raise HTTPException(500, detail={
            'ok': False, 'pesan': 'Naskah tidak bisa dibaca.'})

    ai_mod.peta_mulai = _palsu_gagal_http
    hasil3 = asyncio.run(ai_mod.peta_mulai_latar(
        _ReqPalsu({'file_id': fid}), u, db))
    kode3 = hasil3.get('kode')
    cek('latar: tekan saat gagal lama -> dijadwalkan lagi',
        hasil3.get('dijadwalkan') is True)
    cek('latar: pekerja gagal (status gagal)',
        _tunggu_status(kode3, 'gagal'))
    db.expire_all()
    kea = ai_mod._pemeriksaan_terkini(db, uid, fid, peta_ada=True)
    cek('latar: gagal HTTPException -> keadaan gagal + pesan asli',
        kea['keadaan'] == 'gagal'
        and kea['galat'] == 'Naskah tidak bisa dibaca.', str(kea))

    async def _palsu_gagal_umum(request, uu, d2):
        raise RuntimeError('sesuatu yang teknis sekali: boom 0x42')

    ai_mod.peta_mulai = _palsu_gagal_umum
    hasil4 = asyncio.run(ai_mod.peta_mulai_latar(
        _ReqPalsu({'file_id': fid}), u, db))
    kode4 = hasil4.get('kode')
    cek('latar: pekerja galat umum -> status gagal',
        _tunggu_status(kode4, 'gagal'))
    db.expire_all()
    kea4 = ai_mod._pemeriksaan_terkini(db, uid, fid, peta_ada=True)
    cek('latar: galat umum -> pesan baku Indonesia, tanpa jejak teknis',
        kea4['keadaan'] == 'gagal'
        and kea4['galat'] == 'Pemeriksaan belum berhasil. '
                             'Coba lagi sebentar lagi.'
        and 'boom' not in kea4['galat'], str(kea4))
    ai_mod.peta_mulai = asli_peta_mulai
    db.close()

    print(f'\n{len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL:')
        for g in GAGAL:
            print('  - ' + g)
        sys.exit(1)


if __name__ == '__main__':
    main()
