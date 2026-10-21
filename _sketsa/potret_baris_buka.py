"""Potret halaman tinjau DENGAN BARIS CATATAN DIBUKA.

KENAPA: tombol "Lihat di naskah" ada di dalam `.detail` yang TERLIPAT
(display:none sampai baris diklik). Potret biasa tidak akan melihatnya —
dan itulah sebab MATA pertama bilang "tidak ada tombol".
"""
import json
import sys
import time
import urllib.request

sys.path.insert(0, '/app')

TOK = open('/app/_tok25b.txt').read().strip()
URL = f'http://127.0.0.1:8100/tinjau/{TOK}'

import websocket                                                  # noqa: E402

#  buka tab baru lewat Chrome DevTools Protocol
try:
    ver = json.load(urllib.request.urlopen('http://127.0.0.1:9333/json/version',
                                           timeout=8))
except Exception as e:                                             # noqa: BLE001
    print('  ❌ CDP mati:', e)
    sys.exit(1)

tab = json.load(urllib.request.urlopen(
    f'http://127.0.0.1:9333/json/new?{URL}', timeout=10))
ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=40)
_id = [0]


def kirim(method, **p):
    _id[0] += 1
    ws.send(json.dumps({'id': _id[0], 'method': method, 'params': p}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == _id[0]:
            return r.get('result', {})


time.sleep(4)
#  buka SEMUA baris catatan supaya tombolnya kelihatan
kirim('Runtime.evaluate', expression=(
    "document.querySelectorAll('.baris').forEach(function(b){"
    "  b.classList.add('buka'); });"
    "'dibuka: ' + document.querySelectorAll('.baris.buka').length + "
    "' | tombol: ' + document.querySelectorAll('.tb-tunjuk').length"),
    returnByValue=True)
time.sleep(2)

#  potret layar penuh
hasil = kirim('Page.captureScreenshot', format='png', captureBeyondViewport=True)
import base64
open('/tmp/t25c/01-halaman-buka.png', 'wb').write(
    base64.b64decode(hasil['data']))
print('  ✅ tersimpan: /tmp/t25c/01-halaman-buka.png')
ws.close()
