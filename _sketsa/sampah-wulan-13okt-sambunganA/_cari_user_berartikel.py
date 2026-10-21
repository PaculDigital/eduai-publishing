import sys

sys.path.insert(0, '/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import jurnal as J
from app.models import FileBerkas, ProfilDokumen, User

S = sessionmaker(bind=create_engine(
    'sqlite:////app/data/eduai.db', connect_args={'check_same_thread': False}))

with S() as db:
    for u in db.query(User).order_by(User.id).all():
        bk = db.query(FileBerkas).filter(FileBerkas.user_id == u.id).all()
        if not bk:
            continue
        print(f'user {u.id} "{u.nama}" <{u.email}> — {len(bk)} berkas')
        for b in bk[:3]:
            p = db.query(ProfilDokumen).filter(
                ProfilDokumen.file_id == b.id).first()
            d = J.baca(p)
            bab = {k: len(v or []) for k, v in J._semua_bab(d).items()}
            if bab:
                print(f'    berkas {b.id} "{b.nama}" bab={bab}')
