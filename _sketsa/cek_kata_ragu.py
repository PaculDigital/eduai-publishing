"""CEK KATA RAGU DI HALAMAN NYATA — 11Okt26.

Baca innerText halaman /mulai sesudah alur deteksi dijalankan, lalu
pastikan kata ragu TIDAK ADA dan kalimat penggantinya ADA.
Bukan asumsi — bukti dari halaman sungguhan.
"""
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlparse

CDP = 'http://127.0.0.1:9333'
IP = '172.17.0.8'
FID = 115


def http(p, m='GET'):
    r = urllib.request.Request(CDP + p, method=m)
    with urllib.request.urlopen(r, timeout=20) as x:
        i = x.read().decode().strip()
    if not i:
        return {}
    try:
        return json.loads(i)
    except Exception:
        return {}


class WS:
    def __init__(s, url):
        u = urlparse(url)
        s.s = socket.create_connection((u.hostname, u.port), timeout=30)
        k = base64.b64encode(os.urandom(16)).decode()
        s.s.sendall(('GET %s HTTP/1.1\r\nHost: %s:%s\r\nUpgrade: websocket\r\n'
                     'Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n'
                     'Sec-WebSocket-Version: 13\r\n\r\n'
                     % (u.path, u.hostname, u.port, k)).encode())
        b = b''
        while b'\r\n\r\n' not in b:
            b += s.s.recv(4096)
        s.buf = b.split(b'\r\n\r\n', 1)[1]
        s.n = 0

    def _k(s, t):
        d = t.encode()
        h = bytearray([0x81])
        n = len(d)
        if n < 126:
            h.append(0x80 | n)
        elif n < 65536:
            h.append(0x80 | 126)
            h += struct.pack('>H', n)
        else:
            h.append(0x80 | 127)
            h += struct.pack('>Q', n)
        m = os.urandom(4)
        h += m
        s.s.sendall(bytes(h) + bytes(b ^ m[i % 4] for i, b in enumerate(d)))

    def _b(s):
        while len(s.buf) < 2:
            x = s.s.recv(4096)
            if not x:
                return None
            s.buf += x
        d = s.buf
        p = d[1] & 0x7F
        g = 2
        if p == 126:
            p = struct.unpack('>H', d[2:4])[0]
            g = 4
        elif p == 127:
            p = struct.unpack('>Q', d[2:10])[0]
            g = 10
        while len(d) < g + p:
            x = s.s.recv(65536)
            if not x:
                return None
            d += x
        i = d[g:g + p]
        s.buf = d[g + p:]
        return i.decode('utf-8', 'replace')

    def cmd(s, m, p=None):
        s.n += 1
        i = s.n
        s._k(json.dumps({'id': i, 'method': m, 'params': p or {}}))
        for _ in range(60):
            t = s._b()
            if t is None:
                return {}
            try:
                j = json.loads(t)
            except Exception:
                continue
            if 'id' in j and j['id'] == i:
                return j
        return {}

    def ev(s, e):
        return (s.cmd('Runtime.evaluate',
                      {'expression': e, 'returnByValue': True,
                       'awaitPromise': True})
                .get('result', {}).get('result', {}).get('value'))


tok = subprocess.run(
    ['docker', 'exec', '-i', '-w', '/app', 'eduai-app', 'python3', '-'],
    input=b"import sys;sys.path.insert(0,'/app')\nfrom app.auth import buat_token\nprint(buat_token(8))",
    capture_output=True).stdout.decode().strip()

tab = http('/json/new?about:blank', 'PUT')
ws = WS(tab['webSocketDebuggerUrl'])
ws.cmd('Page.enable')
ws.cmd('Network.enable')
ws.cmd('Network.setCookie', {'name': 'eduai_session', 'value': tok,
                             'url': 'http://%s:8000/' % IP, 'path': '/',
                             'httpOnly': True})
ws.cmd('Page.navigate', {'url': 'http://%s:8000/mulai' % IP})
time.sleep(4)
print('JUDUL HALAMAN:', ws.ev('document.title'))

ws.ev('(async()=>{ await deteksiBerkas(%d); })()' % FID)
time.sleep(6)

teks = ws.ev('document.body.innerText') or ''
print()
print('--- KALIMAT DI LAYAR ---')
print('det-ringkas:', repr(ws.ev("document.getElementById('det-ringkas').innerText")))
print('det-bab    :', repr(ws.ev("document.getElementById('det-bab').innerText")))
print('judul mutu :', repr(ws.ev("document.getElementById('det-mutu-judul').innerText")))

print()
print('--- UJI KATA RAGU ---')
terlarang = ['sepertinya', 'tampaknya', 'nampaknya', 'mungkin', 'kira-kira']
gagal = 0
low = teks.lower()
for k in terlarang:
    ada = k in low
    print(('  ❌ ADA  ' if ada else '  ✅ BERSIH ') + k)
    if ada:
        gagal += 1
        for baris in teks.split('\n'):
            if k in baris.lower():
                print('        →', repr(baris.strip()[:110]))
print()
print('KATA GANTI HARUS ADA:')
for k in ['Terdeteksi', 'sudah lengkap', 'rusak akibat konversi']:
    ada = k in teks
    print(('  ✅ ' if ada else '  ❌ ') + k)
    if not ada:
        gagal += 1

http('/json/close/' + tab['id'])
print()
print('HASIL CEK KATA:', 'LULUS' if gagal == 0 else 'GAGAL (%d)' % gagal)
sys.exit(1 if gagal else 0)
