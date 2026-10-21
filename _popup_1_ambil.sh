#!/bin/bash
# Render popup: AMBIL data dari server → suntik data + auto-buka dalam
# SATU blok script (jangan dua blok — blok kedua menimpa yang pertama).
set -e
cd /opt/data/services/eduai-publishing

# ── TAHAP 1: dalam container, ambil data nyata + HTML naskah ──────────────
docker exec eduai-app python3 -c "
import json, urllib.request, sys
sys.path.insert(0,'/app')
from pathlib import Path
from app.main import buat_token
from app.models import SessionLocal, User
from sqlalchemy import select

API='http://localhost:8000'
def ambil(url, token=None):
    r=urllib.request.Request(API+url)
    if token: r.add_header('Cookie','eduai_session='+token)
    with urllib.request.urlopen(r, timeout=30) as x:
        return json.loads(x.read().decode())

db=SessionLocal()
for nama,email in [('penulis','uji-render-addon@test.local'),
                   ('gratis','uji-render-addon-gratis@test.local')]:
    u=db.scalars(select(User).where(User.email==email)).first()
    T=buat_token(u.id)
    dp=ambil('/api/paket',T); da=ambil('/api/addon',T)
    r=urllib.request.Request(API+'/naskah'); r.add_header('Cookie','eduai_session='+T)
    html=urllib.request.urlopen(r,timeout=45).read().decode('utf-8','replace')

    # SATU blok: data mock + auto-buka. Ditulis ke berkas JSON terpisah
    # supaya tidak ada escaping yang bikin rusak.
    Path('/tmp/pp/data_'+nama+'.json').write_text(json.dumps({'paket':dp,'addon':da}))
    Path('/tmp/pp/base_'+nama+'.html').write_text(html, encoding='utf-8')
    print('  %-8s paket=%d addon=%d boleh_beli=%s html=%d'
          % (nama,len(dp.get('paket',[])),len(da.get('addon',[])),
             da.get('boleh_beli'),len(html)))
db.close()
"
for n in penulis gratis; do
  docker exec eduai-app sh -c "cat /tmp/pp/base_$n.html" > /tmp/pp/base_$n.html
done
echo "  data + HTML terambil"
