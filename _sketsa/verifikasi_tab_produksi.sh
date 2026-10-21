#!/usr/bin/env bash
#  Verifikasi produksi: tab Referensi benar-benar muncul (07 Okt 2026)
cd /opt/data/services/eduai-publishing || exit 1
docker exec -w /app eduai-app timeout 400 python3 -u -c "
import sys, urllib.request, urllib.error
sys.path.insert(0,'/app')
from app import auth as A
from app.models import User, SessionLocal
from sqlalchemy import select
with SessionLocal() as s:
    u = s.execute(select(User)).scalars().first()
tok = A.buat_token(u.id)
print('user uji:', u.email, 'id', u.id, flush=True)
for jalur in ['/naskah','/kolaborasi','/belajar','/referensi','/artikel']:
    try:
        r = urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000'+jalur, headers={'Cookie':'eduai_session='+tok}), timeout=90)
        t = r.read().decode('utf-8','ignore')
        tab = t.count('href=\"/referensi\"')
        art = t.count('href=\"/artikel\"')
        aktif = 'href=\"/referensi\" class=\"aktif\"' in t
        print(f'  {jalur:14} HTTP={r.status} tab-Ref={tab} tab-Artikel={art} aktif={aktif}', flush=True)
    except urllib.error.HTTPError as e:
        print(f'  {jalur:14} HTTP={e.code}', flush=True)
"
