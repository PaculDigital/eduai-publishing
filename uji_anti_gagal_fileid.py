"""Uji G2: backfill job.file_id lewat tandai_selesai, mock DB saja.

Jalankan (python yang punya sqlalchemy, mis. venv uji di /tmp):
  EDUAI_SECRET_KEY=uji-dummy EDUAI_ROUTER_KEY=uji-dummy \
    /tmp/venv_anti_gagal/bin/python3 uji_anti_gagal_fileid.py
Keluar 0 bila semua LULUS, 1 bila ada GAGAL.

JANGAN jalankan dengan DB produksi: uji ini memakai sqlite memory
dan menambal SessionLocal di app.proses, jadi tidak menyentuh DB
produksi sama sekali. Notifikasi juga ditambal, hanya direkam.
"""

import json
import os
import sys
import tempfile

os.environ.setdefault('EDUAI_SECRET_KEY', 'uji-dummy')
os.environ.setdefault('EDUAI_ROUTER_KEY', 'uji-dummy')
_tmp = tempfile.mkdtemp(prefix='uji_g2_')
os.environ.setdefault('EDUAI_DATA_DIR', _tmp)
os.environ.setdefault('EDUAI_UPLOAD_DIR', _tmp)

for p in (os.getcwd(), '/opt/data/services/eduai-publishing'):
    if p and os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import proses as P
from app.models import ProsesAI

LULUS = 0
GAGAL = []


def cek(nama, ok, info=''):
    global LULUS
    if ok:
        LULUS += 1
        print('  LULUS %s' % nama)
    else:
        GAGAL.append(nama)
        print('  GAGAL %s %s' % (nama, info))


def main():
    engine = create_engine('sqlite:///:memory:')
    ProsesAI.__table__.create(engine, checkfirst=True)
    SesiUji = sessionmaker(bind=engine, expire_on_commit=False)
    P.SessionLocal = SesiUji
    notif = []

    def notif_palsu(user_id, nama_jenis, **data):
        notif.append((nama_jenis, data))

    P._simpan_notifikasi = notif_palsu

    s = SesiUji()
    s.add(ProsesAI(kode='UJI-G2', user_id=1, file_id=None,
                   status='jalan', tahap='Menulis',
                   komentar_json='[]', jenis_dokumen='buku',
                   jumlah_bagian=1, panjang=0))
    s.commit()
    s.close()

    # Kasus utama: hasil buku berisi file_id 123 (nilai job 222).
    hasil = {'file_id': 123, 'docx': '/tmp/palsu/buku.docx'}
    P.tandai_selesai('UJI-G2', hasil='Judul Uji',
                     hasil_json=json.dumps(hasil, default=str),
                     file_id=hasil.get('file_id'),
                     jenis_notifikasi='buku_selesai')
    s = SesiUji()
    baris = s.execute(
        __import__('sqlalchemy').select(ProsesAI).where(
            ProsesAI.kode == 'UJI-G2')).scalar_one()
    cek('g2-fileid-123', baris.file_id == 123, repr(baris.file_id))
    cek('g2-status-selesai', baris.status == 'selesai', baris.status)
    cek('g2-notif-bawa-123',
        bool(notif) and notif[0][1].get('file_id') == 123, repr(notif))
    s.close()

    # Kasus jaga: tanpa file_id, file_id lama dibiarkan (alur revisi).
    s = SesiUji()
    s.add(ProsesAI(kode='UJI-G2-LAMA', user_id=1, file_id=77,
                   status='jalan', tahap='Menulis',
                   komentar_json='[]', jenis_dokumen='revisi',
                   jumlah_bagian=1, panjang=0))
    s.commit()
    s.close()
    P.tandai_selesai('UJI-G2-LAMA', hasil='jawaban revisi')
    s = SesiUji()
    baris2 = s.execute(
        __import__('sqlalchemy').select(ProsesAI).where(
            ProsesAI.kode == 'UJI-G2-LAMA')).scalar_one()
    cek('g2-tanpa-fileid-dibiarkan', baris2.file_id == 77,
        repr(baris2.file_id))
    s.close()

    print('LULUS %d, GAGAL %d' % (LULUS, len(GAGAL)))
    return 1 if GAGAL else 0


if __name__ == '__main__':
    raise SystemExit(main())
