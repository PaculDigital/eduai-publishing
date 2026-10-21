#!/usr/bin/env bash
#  UJI SEMUA HALAMAN HIDUP (07 Okt 2026)
cd /opt/data/services/eduai-publishing || exit 1
docker exec -w /app eduai-app timeout 500 python3 -u -c "
import sys, urllib.request, urllib.error
sys.path.insert(0,'/app')
from app import auth as A
from app.models import User, SessionLocal
from sqlalchemy import select
with SessionLocal() as s:
    u = s.execute(select(User)).scalars().first()
tok = A.buat_token(u.id)
hal = ['/', '/naskah','/kolaborasi','/belajar','/referensi','/artikel',
       '/mulai','/pengaturan','/sampah','/masuk','/setelan-wa']
print(f'user uji: {u.email} (id {u.id})', flush=True)
for j in hal:
    try:
        r = urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000'+j,
            headers={'Cookie':'eduai_session='+tok}), timeout=90)
        b = r.read()
        print(f'  {j:16} HTTP={r.status} {len(b):>7} kar', flush=True)
    except urllib.error.HTTPError as e:
        print(f'  {j:16} HTTP={e.code}', flush=True)
    except Exception as e:
        print(f'  {j:16} ERR {type(e).__name__}', flush=True)
"
