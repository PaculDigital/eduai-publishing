"""Uji cepat: /v1/bab balas field `besar` + item `bab` lama utuh."""
import os
import sys
sys.path.insert(0, '/tmp/rg')
os.environ.setdefault('EDUAI_DATA_DIR', '/tmp/rg_data')
os.environ.setdefault('EDUAI_UPLOAD_DIR', '/tmp/rg_up')
from fastapi.testclient import TestClient
from app.auth import buat_token
from app.config import SESSION_COOKIE
from app.main import app

k = TestClient(app)
r = k.post('/api/ai/v1/bab', json={'file_id': 78},
           cookies={SESSION_COOKIE: buat_token(7)})
d = r.json()
bb = d.get('bab') or []
print('kode', r.status_code, 'ok', d.get('ok'))
print('bab halus:', [x['label'] for x in bb])
print('besar    :', [(x['label'], x['panjang'], x.get('anak'))
                     for x in (d.get('besar') or [])])
print('yatim    :', d.get('yatim'))
assert r.status_code == 200 and d.get('ok')
assert [x['label'] for x in bb] == \
    ['1.1', '1.2', '1.3', '1.4', '2.1', '2.2', '3.1', '3.2'], 'item lama berubah!'
assert (d.get('besar') or []), 'field besar kosong'
print('LULUS: bab lama identik + besar terisi')
