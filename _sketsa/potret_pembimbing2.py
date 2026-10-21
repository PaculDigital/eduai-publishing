#!/usr/bin/env python3
"""POTRET LENGKAP HALAMAN PEMBIMBING — identitas → naskah → catatan.

Standar 25Sep26: potret_cdp.py (socket mentah · CDP :9333) · profil baru.
"""
import base64
import json
import os
import socket
import time
import urllib.request

CDP = 'http://127.0.0.1:9333'
BASE = 'https://eduai.bikinaja.id'
TOKEN = 'sjGg7kYVQozl4y9p-WvSouU-fk-jBQo-hPaDJhjsCjg'
KELUAR = ('/opt/data/services/eduai-publishing/_sketsa/bukti_sinkron')
os.makedirs(KELUAR, exist_ok=True)


class T:
    def __init__(s, lb=1500, tg=1300):
        req = urllib.request.Request(f'{CDP}/json/new?about:blank',
                                     method='PUT')
        try:
            t = json.loads(urllib.request.urlopen(req, timeout=15).read())
        except Exception:                                                 # noqa: BLE001
            t = json.loads(urllib.request.urlopen(
                f'{CDP}/json/new?about:blank', timeout=15).read())
        s.tid = t['id']
        hp, path = t['webSocketDebuggerUrl'].split('://', 1)[1].split('/', 1)
        s.s = socket.create_connection(
            (hp.split(':')[0], int(hp.split(':')[1])), timeout=90)
        k = base64.b64encode(os.urandom(16)).decode()
        s.s.sendall((
            f'GET /{path} HTTP/1.1\r\nHost: {hp}\r\nUpgrade: websocket\r\n'
            f'Connection: Upgrade\r\nSec-WebSocket-Key: {k}\r\n'
            'Sec-WebSocket-Version: 13\r\n\r\n').encode())
        b = b''
        while b'\r\n\r\n' not in b:
            b += s.s.recv(4096)
        s.i = 0
        s.lb, s.tg = lb, tg

    def kr(s, m, p):
        s.i += 1
        d = json.dumps({'id': s.i, 'method': m, 'params': p or {}}).encode()
        mk = os.urandom(4)
        tp = bytes(x ^ mk[j % 4] for j, x in enumerate(d))
        h = (bytes([0x81, 0x80 | len(d)]) if len(d) < 126
             else bytes([0x81, 0x80 | 126]) + len(d).to_bytes(2, 'big'))
        s.s.sendall(h + mk + tp)
        return s.i

    def tr(s):
        h = s.s.recv(2)
        if not h:
            return None
        n = h[1] & 0x7F
        if n == 126:
            n = int.from_bytes(s.s.recv(2), 'big')
        elif n == 127:
            n = int.from_bytes(s.s.recv(8), 'big')
        d = b''
        while len(d) < n:
            d += s.s.recv(n - len(d))
        return json.loads(d)

    def cmd(s, m, p=None):
        pid = s.kr(m, p)
        for _ in range(400):
            r = s.tr()
            if r is None:
                return None
            if r.get('id') == pid:
                return r
        return None

    def js(s, e):
        r = s.cmd('Runtime.evaluate', {'expression': e, 'returnByValue': True,
                                       'awaitPromise': True})
        try:
            return r['result']['result'].get('value')
        except Exception:                                                 # noqa: BLE001
            return None

    def ke(s, url, t=8):
        s.cmd('Page.enable')
        s.cmd('Page.navigate', {'url': url})
        time.sleep(t)
        s.cmd('Emulation.setDeviceMetricsOverride', {
            'width': s.lb, 'height': s.tg, 'deviceScaleFactor': 1,
            'mobile': False})
        time.sleep(1.5)

    def potret(s, n):
        r = s.cmd('Page.captureScreenshot', {'format': 'png'})
        if not (r and r.get('result', {}).get('data')):
            print(f'  ❌ {n}')
            return None
        j = os.path.join(KELUAR, n)
        open(j, 'wb').write(base64.b64decode(r['result']['data']))
        print(f'  ✅ {n} — {os.path.getsize(j)} byte')
        return j

    def tutup(s):
        try:
            s.s.close()
        except Exception:                                                 # noqa: BLE001
            pass
        try:
            urllib.request.urlopen(f'{CDP}/json/close/{s.tid}', timeout=10).read()
        except Exception:                                                 # noqa: BLE001
            pass


def teks(t, n=700):
    return t.js("(()=>{const b=document.body.innerText||'';"
                f"return b.replace(/\\s+/g,' ').slice(0,{n})}})()")


print('══ 1. HALAMAN UNDANGAN (identitas) ══')
t = T()
t.ke(f'{BASE}/tinjau/{TOKEN}')
print('  judul:', t.js('document.title'))
print('  TEKS :', teks(t, 400))
t.potret('pmb-01-undangan.png')
t.tutup()

print()
print('══ 2. ISI IDENTITAS → LANJUT ══')
t = T()
t.ke(f'{BASE}/tinjau/{TOKEN}')
#  isi field identitas lalu klik Lanjut
t.js("(()=>{const i=document.querySelector('input[name=identitas]');"
     "if(i){i.value='0812-0000-0000 (uji mata)';"
     "i.dispatchEvent(new Event('input',{bubbles:true}));}"
     "const b=document.querySelector('button[type=submit]');"
     "if(b)b.click();return true})()")
time.sleep(7)
print('  judul sesudah:', t.js('document.title'))
print('  TEKS :', teks(t, 900))
t.potret('pmb-02-sesudah-identitas.png')
t.tutup()

print()
print('══ 3. HALAMAN NASKAH PEMBIMBING ══')
t = T()
t.ke(f'{BASE}/tinjau/{TOKEN}')
naskah = t.js("(()=>{const a=[...document.querySelectorAll('a')]"
              ".map(e=>e.getAttribute('href')||'')"
              ".filter(h=>h.includes('/naskah/'));return a.slice(0,4)})()")
print('  tautan naskah:', naskah)
if not naskah:
    naskah = t.js("(()=>{const a=[...document.querySelectorAll('a')]"
                  ".map(e=>({h:e.getAttribute('href')||'',"
                  "t:(e.textContent||'').trim().slice(0,30)}));"
                  "return JSON.stringify(a.slice(0,20))})()")
    print('  semua tautan:', naskah)
if naskah and isinstance(naskah, list) and naskah:
    t.ke(f'{BASE}{naskah[0]}', 12)
    print('  judul:', t.js('document.title'))
    print('  TEKS :', teks(t, 1200))
    t.potret('pmb-03-naskah.png')
t.tutup()
print()
print('SELESAI')
