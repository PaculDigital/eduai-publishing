"""Diagnosa 4: kutip 'hipotesis yaitu' ada di region ambil_bab('3.1')?"""
import os, sys
sys.path.insert(0, '/tmp/rg')
os.environ.setdefault('EDUAI_DATA_DIR', '/tmp/rg_data')
os.environ.setdefault('EDUAI_UPLOAD_DIR', '/tmp/rg_up')

from app.ai import _teks_dari_body
from app.versi import ambil_bab, _deteksi_bagian, susun_ulang
from app.models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_db = sessionmaker(bind=create_engine('sqlite:////tmp/rg_data/eduai.db'))()
_u = _db.query(User).filter(User.id == 7).first()
NASKAH, _, _err = _teks_dari_body(_db, _u, {'file_id': 78})
KUTIP = 'hipotesis yaitu hipotesis komparatif yang berarti potensi untuk memberikan jawaban'

sebelum, isi31, sesudah = ambil_bab(NASKAH, '3.1')
print('isi31 len =', len(isi31))
print('kutip ∈ isi31?', KUTIP in isi31)
print('posisi kutip di naskah =', NASKAH.find(KUTIP))
print('posisi awal isi31 =', NASKAH.find(isi31[:60]) if isi31 else -1)

#  paragraf: bagaimana pipa memecah? pakai pisah_paragraf milik pipa
from app.pipa import pisah_paragraf, cari_paragraf
par = pisah_paragraf(isi31)
print('jumlah paragraf (pisah_paragraf) =', len(par))
idx, keadaan, skor = cari_paragraf(par, KUTIP)
print('cari_paragraf →', keadaan, 'idx=', idx, 'skor=', skor)
if keadaan != 'ada':
    for i, p in enumerate(par[:12]):
        print(f'  par[{i}] ({len(p)} kar): {p[:90]!r}')

#  bandingkan dengan naskah UTUH (F3 lolos pakai naskah utuh)
par2 = pisah_paragraf(NASKAH)
idx2, ke2, skor2 = cari_paragraf(par2, KUTIP)
print('cari_paragraf di NASKAH UTUH →', ke2, 'idx=', idx2)
