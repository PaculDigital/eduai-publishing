"""POTRET LAYAR DETEKSI /mulai — uji tampilan MUTU NASKAH sungguhan.

Cara: buat akun uji → unggah naskah (rusak & sehat) → panggil alur/petakan →
potret layar deteksi lewat CDP (Chrome :9333).

Jalankan DI DALAM container? TIDAK — Butuh Chrome di HOST. Jalankan di host,
server :8000 diakses via 127.0.0.1 (port dibuka host? cek dulu).
"""
from __future__ import annotations

import base64
import json
import sys
import time
import urllib.parse
import urllib.request

import websocket

CDP = 'http://127.0.0.1:9333'
BASE = 'http://127.0.0.1:8100'


def ws_baru(url):
    req = urllib.request.Request(
        CDP + '/json/new?' + urllib.parse.quote(url, safe=''), method='PUT')
    x = json.loads(urllib.request.urlopen(req, timeout=20).read())
    return x.get('id'), x.get('webSocketDebuggerUrl')


def main():
    url = sys.argv[1]
    keluar = sys.argv[2]
    tid, wsurl = ws_baru(url)
    ws = websocket.create_connection(wsurl, timeout=40, suppress_origin=True)

    def kirim(i, method, **p):
        ws.send(json.dumps({'id': i, 'method': method, 'params': p}))
        while True:
            m = json.loads(ws.recv())
            if m.get('id') == i:
                return m

    kirim(1, 'Emulation.setDeviceMetricsOverride', width=430, height=2400,
          deviceScaleFactor=2, mobile=True)
    time.sleep(4)
    r = kirim(2, 'Runtime.evaluate', returnByValue=True,
              expression='document.body.scrollHeight')
    sh = r.get('result', {}).get('result', {}).get('value') or 2400
    kirim(3, 'Emulation.setDeviceMetricsOverride', width=430,
          height=min(int(sh) + 40, 12000), deviceScaleFactor=2, mobile=True)
    time.sleep(1.5)
    r = kirim(4, 'Page.captureScreenshot', format='png',
              captureBeyondViewport=True)
    data = r.get('result', {}).get('data')
    open(keluar, 'wb').write(base64.b64decode(data))
    print('tersimpan:', keluar)
    ws.close()


if __name__ == '__main__':
    main()
