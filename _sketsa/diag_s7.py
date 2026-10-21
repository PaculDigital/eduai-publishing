"""Diagnosa 3: isi potongan peta 3.1 & 3.2 — di mana 'hipotesis yaitu' berada?"""
import os
import sys
APP_ROOT = '/tmp/rg'
sys.path.insert(0, APP_ROOT)
os.environ.setdefault('EDUAI_DATA_DIR', '/tmp/rg_data')
os.environ.setdefault('EDUAI_UPLOAD_DIR', '/tmp/rg_up')

from app.ai import _teks_dari_body
from app.versi import _deteksi_bagian, ambil_bab
from app.models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_db = sessionmaker(bind=create_engine('sqlite:////tmp/rg_data/eduai.db'))()
_u = _db.query(User).filter(User.id == 7).first()
NASKAH, _fb, _err = _teks_dari_body(_db, _u, {'file_id': 78})
if _err:
    print('berkas tak terbaca:', _err)
    sys.exit(3)

b = _deteksi_bagian(NASKAH)
pos = {str(x.get('label')): x['posisi'] for x in b}
print('posisi peta 3.1 =', pos.get('3.1'), '| 3.2 =', pos.get('3.2'))

i = NASKAH.find('hipotesis yaitu hipotesis komparatif')
print('posisi kutip "hipotesis yaitu" =', i,
      '| di region 3.1?', pos.get('3.1', 0) <= i < pos.get('3.2', 0),
      '| di region 3.2?', i >= pos.get('3.2', 0))

p31, p32 = pos.get('3.1', 0), pos.get('3.2', 0)
isi31 = ambil_bab(NASKAH, '3.1')
isi32 = ambil_bab(NASKAH, '3.2')
print('\nambıl_bab("3.1") len =', len(isi31))
print('  awal 160:', repr(isi31[:160]))
print('  akhir 160:', repr(isi31[-160:]))
print('  kutip ada di isi31?', 'hipotesis yaitu hipotesis komparatif' in isi31)
print('\nambıl_bab("3.2") len =', len(isi32))
print('  awal 160:', repr(isi32[:160]))
print('  kutip ada di isi32?', 'hipotesis yaitu hipotesis komparatif' in isi32)

#  bandingkan dengan slice peta langsung
print('\nslice peta [p31:p32] len =', p32 - p31,
      '| sama dengan ambil_bab?', NASKAH[p31:p32] == isi31)
