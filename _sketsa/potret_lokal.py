"""Potret berkas HTML lokal — AKTIFKAN tab dulu (penyebab 'Unable to capture')."""
import json, time, os, base64, urllib.request
from websocket import create_connection

CDP = 'http://127.0.0.1:9333'
URL = 'file:///tmp/uji_ikon_aksi.html'
OUT = '/opt/data/services/eduai-publishing/_potret/sketsa-ikon/07-ikon-tampilan-penuh.png'

req = urllib.request.Request(CDP + '/json/new?' + URL, method='PUT')
t = None
for _ in range(20):
    try:
        t = json.loads(urllib.request.urlopen(req, timeout=8).read()); break
    except Exception:
        time.sleep(1)
if not t:
    raise SystemExit('CDP mati')
print('tab:', t.get('id'), t.get('url'))

ws = create_connection(t['webSocketDebuggerUrl'], timeout=60)
_i = [0]

def cmd(m, **p):
    _i[0] += 1
    ws.send(json.dumps({'id': _i[0], 'method': m, 'params': p}))
    while True:
        d = json.loads(ws.recv())
        if d.get('id') == _i[0]:
            return d

cmd('Page.enable')
#  ⚠️ AKAR 'Unable to capture screenshot': tab belum terlihat (hidden/inactive).
#  Obat: bawa tab ini ke depan DULU.
cmd('Page.bringToFront')
time.sleep(2.5)
r = cmd('Page.captureScreenshot', format='png', captureBeyondViewport=True)
if 'result' not in r or 'data' not in r.get('result', {}):
    print('MASIH GAGAL:', json.dumps(r)[:300]); raise SystemExit(1)
b = base64.b64decode(r['result']['data'])
open(OUT, 'wb').write(b)
print(f'✓ {OUT} ({len(b)} byte)')
