#!/bin/bash
# Render TANPA pemicu URL -> supaya TOMBOL ADDON di peringatan kuning
# terlihat (tidak tertutup popup). Ini bukti gerbang folder bagian tombol.
cd /opt/data/services/eduai-publishing || exit 1

docker exec eduai-app python3 -c "
import json, sys, urllib.request
sys.path.insert(0,'/app')
from pathlib import Path
from app.main import buat_token
from app.models import SessionLocal, User
from sqlalchemy import select
db=SessionLocal()
u=db.scalars(select(User).where(User.email=='uji-gg@test.local')).first()
T=buat_token(u.id)
def ambil(url):
    r=urllib.request.Request('http://localhost:8000'+url)
    r.add_header('Cookie','eduai_session='+T)
    with urllib.request.urlopen(r,timeout=40) as x: return x.read().decode('utf-8','replace')
# TANPA ?addon=storage -> popup TIDAK terbuka
html=ambil('/naskah')
Path('/tmp/gg/tombol.html').write_text(html, encoding='utf-8')
print('  tombol.html %s byte | tombol addon=%d' % (len(html), html.count('fd-tombol-addon')))
db.close()
"
docker exec eduai-app sh -c "cat /tmp/gg/tombol.html" > /tmp/gg/tombol.html
echo "  host: $(stat -c%s /tmp/gg/tombol.html) byte"
timeout 150 /opt/data/chrome/chrome --headless=new --no-sandbox --disable-gpu \
  --hide-scrollbars --window-size=900,1000 --screenshot=/tmp/gg/tombol.png \
  --virtual-time-budget=4000 "file:///tmp/gg/tombol.html" 2>/dev/null
echo "  tombol.png -> $(stat -c%s /tmp/gg/tombol.png 2>/dev/null || echo GAGAL) byte"
