"""Diagnosa 2: apa isi 84468..86143 di sekitar penanda '3.1.' — batas pembuka benar atau salah?"""
import sys

sys.path.insert(0, '/tmp/rg')
from app.ai import _teks_dari_body                              # noqa: E402
from app.versi import ambil_bab, ambil_pembuka, deteksi_bab      # noqa: E402
from app.models import User                                     # noqa: E402
from sqlalchemy import create_engine                            # noqa: E402
from sqlalchemy.orm import sessionmaker                         # noqa: E402

db = sessionmaker(bind=create_engine('sqlite:////tmp/rg_data/eduai.db'))()
u = db.query(User).filter(User.id == 7).first()
N, _, _ = _teks_dari_body(db, u, {'file_id': 78})

print('=== sekitar literal "3.1." (84511) ===')
print(repr(N[84440:84640]))
print()
print('=== sekitar posisi deteksi 3.1 (86143) ===')
print(repr(N[86040:86320]))
print()
print('=== daftar deteksi_bab ===')
for b in deteksi_bab(N):
    print(' ', b.get('label'), 'posisi=', b.get('posisi'),
          'akhir=', b.get('akhir'), 'judul=', repr(b.get('judul'))[:60])
print()
s, i, ss = ambil_pembuka(N, 'BAB III')
print('pembuka: sebelum=', len(s), 'isi=', len(i), 'sesudah=', len(ss))
print('pembuka TAIL:', repr(i[-260:]))
print()
_, i31, _ = ambil_bab(N, '3.1')
print('3.1 HEAD:', repr(i31[:200]))
