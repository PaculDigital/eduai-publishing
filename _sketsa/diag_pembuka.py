"""Diagnosa cepat jalur 1/2: geometri pembuka vs label 3.1 + kandidat paragraf stub."""
import os
import re
import sys

sys.path.insert(0, '/tmp/rg')
from app.ai import _teks_dari_body                              # noqa: E402
from app.versi import ambil_bab, ambil_pembuka, _deteksi_bagian  # noqa: E402
from app.models import User                                     # noqa: E402
from sqlalchemy import create_engine                            # noqa: E402
from sqlalchemy.orm import sessionmaker                         # noqa: E402

db = sessionmaker(bind=create_engine('sqlite:////tmp/rg_data/eduai.db'))()
u = db.query(User).filter(User.id == 7).first()
N, _, _ = _teks_dari_body(db, u, {'file_id': 78})

for b in _deteksi_bagian(N):
    if str(b.get('label')).startswith('3.'):
        print('bagian', b.get('label'), 'posisi=', b.get('posisi'),
              'akhir=', b.get('akhir'), 'judul=', repr(b.get('judul'))[:70])
print('literal "3.1." posisi =', N.find('3.1.'))
print('literal "3.2"  posisi =', N.find('3.2'))
s, i, ss = ambil_pembuka(N, 'BAB III')
print('pembuka len=', len(i), 'batas=', len(s) + len(i),
      'tail=', repr(i[-90:]))
_, i31, _ = ambil_bab(N, '3.1')
_, i32, _ = ambil_bab(N, '3.2')
print('len 3.1=', len(i31), 'len 3.2=', len(i32),
      'sum=', len(i31) + len(i32), 'sesudah=', len(ss))

for nama, t in (('pembuka', i), ('3.1', i31), ('3.2', i32), ('bab3', N)):
    k = [p.strip() for p in re.split(r'\n+', t) if len(p.split()) >= 12]
    print(f'par>=12 kata di {nama}: {len(k)}; terpanjang='
          f'{len(max(k, key=len)) if k else 0} kar')
    if k:
        print('   contoh:', max(k, key=len)[:130])
