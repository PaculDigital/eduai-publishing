"""Potret layar deteksi /mulai (lewat CDP :9333) — pakai login sungguhan.

Cara kerja: nyalakan halaman login, isi form, unggah naskah rusak, lalu
potret layar deteksi. Kalau langkah rumit, minimal: potret /mulai.
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
BASE = 'http://172.17.0.10:8000'


def tab(url: str):
    req = urllib.request.Request(
        CDP + '/json/new?' + urllib.parse.quote(url, safe=''), method='PUT')
    x = json.loads(urllib.request.urlopen(req, timeout=20).read())
    return x['webSocketDebuggerUrl']


def main():
    keluar = sys.argv[1]
    ws = websocket.create_connection(tab(BASE + '/mulai'), timeout=40,
                                     suppress_origin=True)
    n = [0]

    def k(method, **p):
        n[0] += 1
        ws.send(json.dumps({'id': n[0], 'method': method, 'params': p}))
        while True:
            m = json.loads(ws.recv())
            if m.get('id') == n[0]:
                return m

    k('Emulation.setDeviceMetricsOverride', width=430, height=1200,
      deviceScaleFactor=2, mobile=True)
    time.sleep(3)
    print('URL :', k('Runtime.evaluate', returnByValue=True,
                     expression='location.href')['result']['result']['value'])
    print('isi :', (k('Runtime.evaluate', returnByValue=True,
                      expression='document.body.innerText')['result']['result']
                    ['value'] or '')[:300])
    sh = k('Runtime.evaluate', returnByValue=True,
           expression='document.body.scrollHeight')['result']['result']['value']
    k('Emulation.setDeviceMetricsOverride', width=430,
      height=min(int(sh or 1200) + 30, 8000), deviceScaleFactor=2, mobile=True)
    time.sleep(1.5)
    r = k('Page.captureScreenshot', format='png', captureBeyondViewport=True)
    open(keluar, 'wb').write(base64.b64decode(r['result']['data']))
    print('tersimpan:', keluar)
    ws.close()


if __name__ == '__main__':
    main()
