#!/usr/bin/env python3
"""Uji antrean admin di DB ASLI (sqlite sementara, 15 Nov 2026).

Jalankan `python3 tests/test_antrean_db.py`, keluar 0 bila semua lulus.
Memakai model asli + `app.antrean` asli (bukan stub): tabel dibuat di
direktori sementara lewat EDUAI_DATA_DIR, DB produksi tidak tersentuh.

Yang diuji:
  1. tabel `antrean_peta` terbentuk lewat `init_db` (create_all).
  2. `isi_antrean`: baris ragu/curiga masuk; dipanggil 2x -> tidak duplikat.
  3. `putuskan`: satu keputusan terekam + label di peta tersimpan ikut
     diperbarui; 'lewati' merekam tanpa mengubah label; pilihan tidak
     dikenal ditolak.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_antrean_')
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


def cek(nama, benar):
    (LULUS if benar else GAGAL).append(nama)
    print(('  LULUS  ' if benar else '  GAGAL  ') + nama)


def main():
    from app import antrean as an
    from app.models import (AntreanPeta, FileBerkas, ProfilDokumen,
                            SessionLocal, User, init_db)

    init_db()
    db = SessionLocal()
    u = User(email='uji@contoh.id', password_hash='x', nama='Asih')
    db.add(u)
    db.commit()
    fb = FileBerkas(user_id=u.id, nama='SKRIPSI-Asih.docx',
                    nama_simpan='skripsi.docx', ukuran=1000)
    db.add(fb)
    db.commit()

    baris = ['BAB I PENDAHULUAN', 'Isi pendahuluan.',
             '1.1 Latar Belakang', 'Isi latar belakang.',
             'BAB II TINJAUAN PUSTAKA']
    simpan = {
        'ok': True,
        'peta_surveyor': {
            'baris': baris,
            'label': {'0': 'bab', '1': 'paragraf', '2': 'subbab',
                      '3': 'paragraf', '4': 'bab'}},
        'hakim_bagian': [
            {'i': 2, 'label': 'subbab', 'status': 'ragu',
             'teks': '1.1 Latar Belakang'},
            {'i': 4, 'label': 'bab', 'status': 'curiga',
             'teks': 'BAB II TINJAUAN PUSTAKA'},
            {'i': 0, 'label': 'bab', 'status': 'sepakat',
             'teks': 'BAB I PENDAHULUAN'}],
    }
    prof = ProfilDokumen(file_id=fb.id, user_id=u.id,
                         peta_json=json.dumps(simpan, ensure_ascii=False),
                         peta_sidik='sidik123')
    db.add(prof)
    db.commit()

    cek('db: tabel antrean_peta terbentuk',
        db.query(AntreanPeta).count() == 0)

    n1 = an.isi_antrean(db, file_id=fb.id, user_id=u.id,
                        peta_sidik='sidik123', simpan=simpan)
    cek('db: isi_antrean memasukkan 2 baris (ragu + curiga)',
        n1 == 2 and db.query(AntreanPeta).count() == 2)
    n2 = an.isi_antrean(db, file_id=fb.id, user_id=u.id,
                        peta_sidik='sidik123', simpan=simpan)
    cek('db: isi_antrean 2x tidak menduplikasi',
        n2 == 0 and db.query(AntreanPeta).count() == 2)

    rows = db.query(AntreanPeta).order_by(AntreanPeta.baris_idx).all()
    cek('db: baris antrean membawa teks + tetangga + label Jev',
        rows[0].teks == '1.1 Latar Belakang'
        and rows[0].label_jev == 'subbab'
        and rows[0].status_hakim == 'ragu'
        and 'Isi pendahuluan.' in rows[0].tetangga
        and rows[0].status == 'menunggu')

    r = an.putuskan(db, antrean_id=rows[0].id, keputusan='subbab',
                    admin_id=u.id)
    db.refresh(rows[0])
    cek('db: putuskan subbab -> keputusan terekam',
        r['ok'] and rows[0].status == 'diputuskan'
        and rows[0].keputusan == 'subbab'
        and rows[0].diputuskan_oleh == u.id
        and rows[0].diputuskan_pada is not None)
    db.refresh(prof)
    label_baru = json.loads(prof.peta_json)['peta_surveyor']['label']
    cek('db: label di peta tersimpan ikut diperbarui ke pilihan admin',
        label_baru.get('2') == 'subbab')

    r = an.putuskan(db, antrean_id=rows[1].id, keputusan='lewati',
                    admin_id=u.id)
    db.refresh(rows[1])
    db.refresh(prof)
    label_baru = json.loads(prof.peta_json)['peta_surveyor']['label']
    cek('db: lewati -> status dilewati, label peta TIDAK berubah',
        r['ok'] and rows[1].status == 'dilewati'
        and rows[1].keputusan == 'lewati'
        and label_baru.get('4') == 'bab')

    r = an.putuskan(db, antrean_id=rows[0].id, keputusan='salah',
                    admin_id=u.id)
    cek('db: pilihan tidak dikenal ditolak',
        not r['ok'])
    r = an.putuskan(db, antrean_id=999999, keputusan='bab', admin_id=u.id)
    cek('db: butir tidak ada ditolak',
        not r['ok'])
    db.close()

    print(f'\n{len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL:')
        for g in GAGAL:
            print('  - ' + g)
        sys.exit(1)


if __name__ == '__main__':
    main()
