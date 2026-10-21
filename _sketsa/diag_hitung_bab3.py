"""Kenapa /v1/hitung utk bab='BAB III' balas 1, bukan 3? (30Sep26)"""
import os
import sys
sys.path.insert(0, '/tmp/rg')
os.environ.setdefault('EDUAI_DATA_DIR', '/tmp/rg_data')
os.environ.setdefault('EDUAI_UPLOAD_DIR', '/tmp/rg_up')
from fastapi.testclient import TestClient
from app.auth import buat_token
from app.config import SESSION_COOKIE
from app.main import app
from app.models import SessionLocal, User
from app.versi import harga_flat, deteksi_bab
from app.ai import _harga_flat_ai, _teks_dari_body
from app.state import petakan, buang_daftar_isi

db = SessionLocal()
u = db.query(User).filter(User.id == 7).first()
naskah, _fb, _err = _teks_dari_body(db, u, {'file_id': 78})
print('naskah:', len(naskah), 'err:', _err)

print('harga_flat(BAB III, "")       =', harga_flat(naskah, 'BAB III', ''))
print('harga_flat(BAB III, pembuka)  =', harga_flat(naskah, 'BAB III',
                                                    'pembuka'))
print('_harga_flat_ai(BAB III, "")   =', _harga_flat_ai(naskah, 'BAB III',
                                                        ''))
peta = petakan(buang_daftar_isi(naskah))
print('sub-bab petakan:',
      [e['section_id'] for e in peta
       if '.' in str(e.get('section_id') or '')])
print('deteksi_bab:', [(b['label'], b['posisi'], b['akhir'])
                       for b in deteksi_bab(naskah)])

k = TestClient(app)
for body in ({'file_id': 78, 'bab': 'BAB III'},
             {'file_id': 78, 'bab': 'BAB III', 'lingkup': 'bab'}):
    r = k.post('/api/ai/v1/hitung', json=body,
               cookies={SESSION_COOKIE: buat_token(7)})
    d = r.json()
    print('body', body)
    print('   →', r.status_code, 'revisi_dibutuhkan=',
          d.get('revisi_dibutuhkan'), 'bagian=', d.get('bagian'),
          'harga=', d.get('harga'), 'bab=', d.get('bab'))
    print('   pesan=', d.get('pesan'))
db.close()
