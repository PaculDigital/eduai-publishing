"""Potret halaman tinjau DENGAN BARIS CATATAN DIBUKA (dijalankan di `hermes`).

KENAPA PERLU: tombol "Lihat di naskah" ada di dalam `.detail` yang TERLIPAT
(display:none sampai baris diklik). Potret biasa tidak melihatnya — dan
itulah sebab MATA pertama bilang "tidak ada tombol".

Pakai: python3 potret_buka.py <TOKEN> [folder]
"""
import base64
import json
import sys
import time
import urllib.request

import websocket

TOK = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/t25c'
URL = f'http://eduai-app:8000/tinjau/{TOK}'

print('  buka tab:', URL)
tab = json.load(urllib.request.urlopen(
    f'http://127.0.0.1:9333/json/new?{URL}', timeout=10))
ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=60)
_id = [0]


def kirim(method, **p):
    _id[0] += 1
    ws.send(json.dumps({'id': _id[0], 'method': method, 'params': p}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == _id[0]:
            return r.get('result', {})


kirim('Page.enable')
kirim('Runtime.enable')
time.sleep(5)

#  buka SEMUA baris catatan supaya tombolnya kelihatan (persis seperti
#  yang dilakukan pembimbing: klik baris → detail terbuka)
r = kirim('Runtime.evaluate', expression=(
    "document.querySelectorAll('.baris').forEach(function(b){"
    "  b.classList.add('buka'); });"
    "JSON.stringify({baris: document.querySelectorAll('.baris').length,"
    " buka: document.querySelectorAll('.baris.buka').length,"
    " tombol: document.querySelectorAll('.tb-tunjuk').length,"
    " tidak: document.querySelectorAll('.tunjuk-tidak').length})"),
    returnByValue=True)
print('  keadaan halaman:', r.get('result', {}).get('value'))
time.sleep(2)

hasil = kirim('Page.captureScreenshot', format='png',
              captureBeyondViewport=True)
open(f'{OUT}/01-halaman-buka.png', 'wb').write(
    base64.b64decode(hasil['data']))
print('  ✅ tersimpan:', f'{OUT}/01-halaman-buka.png')
ws.close()
