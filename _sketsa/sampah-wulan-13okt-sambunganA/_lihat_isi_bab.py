import sys

sys.path.insert(0, '/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import jurnal as J
from app.models import FileBerkas, ProfilDokumen, User

S = sessionmaker(bind=create_engine(
    'sqlite:////app/data/eduai.db', connect_args={'check_same_thread': False}))

with S() as db:
    u = db.query(User).filter(User.email == 'potret-ref@eduai.test').first()
    print('user uji id:', u.id if u else None)
    if not u:
        sys.exit('user tidak ada')
    for b in db.query(FileBerkas).filter(FileBerkas.user_id == u.id).all():
        p = db.query(ProfilDokumen).filter(
            ProfilDokumen.file_id == b.id).first()
        d = J.baca(p)
        ringkas = {k: len(v or []) for k, v in J._semua_bab(d).items()}
        print(f'  berkas {b.id:>4} "{b.nama}"')
        print(f'        profil={p.id if p else None}  bab={ringkas}')
        for nama in ('BAB I', 'BAB III'):
            lst = J.daftar(d, nama)
            for a in lst:
                print(f'        [{nama}] {a.get("title","")[:52]}'
                      f' | kunci={J.kunci(a)}')
