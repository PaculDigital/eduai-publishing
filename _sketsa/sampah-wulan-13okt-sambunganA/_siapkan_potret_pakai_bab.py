import os
import sys

sys.path.insert(0, '/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import jurnal as J
from app.models import FileBerkas, ProfilDokumen, User

url = os.environ.get('DATABASE_URL', 'sqlite:////app/data/eduai.db')
print('db:', url)
eng = create_engine(url, connect_args={'check_same_thread': False})
S = sessionmaker(bind=eng)

with S() as db:
    u = db.query(User).filter(User.email == 'potret-ref@eduai.test').first()
    print('user uji :', u.id if u else 'TIDAK ADA')
    if not u:
        sys.exit(1)
    berkas = db.query(FileBerkas).filter(FileBerkas.user_id == u.id).first()
    print('berkas   :', berkas.id if berkas else 'TIDAK ADA',
          (berkas.nama if berkas else ''))
    prof = db.query(ProfilDokumen).filter(
        ProfilDokumen.file_id == berkas.id).first()
    print('profil   :', prof.id if prof else 'TIDAK ADA')
    d = J.baca(prof)
    print('bab      :', list((d.get('bab') or {}).keys()))

    #  ── taruh artikel di BAB III + BAB I (kalau belum ada) ──
    ART = [
        {'title': 'Keaslian Streamer terhadap Pembelian Impulsif pada Live '
                  'Streaming Commerce', 'authors': 'Susanti, A.; Rahma, D.',
         'year': '2024', 'journal': 'Jurnal Manajemen Retail',
         'doi': '10.1000/uji.potret.1', 'doi_status': 'verified',
         'abstract': 'Penelitian ini menguji pengaruh keaslian streamer '
                     'terhadap pembelian impulsif pada belanja langsung.'},
        {'title': 'Interaksi Parasosial dan Kepercayaan Penonton',
         'authors': 'Wijaya, B.', 'year': '2023',
         'journal': 'Jurnal Komunikasi Digital', 'doi': '10.1000/uji.potret.2',
         'doi_status': 'verified',
         'abstract': 'Interaksi parasosial terbukti memperkuat kepercayaan '
                     'penonton pada penjual daring.'},
    ]
    if not J.daftar(d, 'BAB III'):
        d = J.tambah(d, 'BAB III', ART, asal='ai')
    if not J.daftar(d, 'BAB I'):
        d = J.tambah(d, 'BAB I', ART[:1], asal='ai')
    prof.jurnal_json = __import__('json').dumps(d, ensure_ascii=False)
    db.commit()
    print('bab SESUDAH:', list((d.get('bab') or {}).keys()))
    print('artikel BAB III:', len(J.daftar(d, 'BAB III')))
    print('artikel BAB I  :', len(J.daftar(d, 'BAB I')))
    print('KUNCI BAB III  :', J.kunci(J.daftar(d, 'BAB III')[0]))
    print('FILE_ID        :', berkas.id)
