"""UJI PRODUKSI v2 — pantau sampai Editor.bin termuat atau habis waktu.

Pelajaran: potret dtk 75 masih "loading" ⇒ JANGAN simpulkan dari iframe saja.
Pantau: (a) apakah judul loading hilang, (b) apakah modal -4 muncul,
(c) apakah Editor.bin diminta (dicek dari log app, di luar skrip ini).
"""
import base64
import json
import os
import socket
import struct
import subprocess
import time
import urllib.request

DOMAIN = 'eduai.bikinaja.id'
FID, USER = 9, 3


def http(p, metode=None):
    r = urllib.request.Request('http://127.0.0.1:9333' + p, method=metode)
    with urllib.request.urlopen(r, timeout=10) as x:
        return json.loads(x.read().decode() or '{}')


class WS:
    def __init__(s, url):
        _, rest = url.split('://', 1)
        host, path = rest.split('/', 1)
        h, p = host.split(':')
        s.s = socket.create_connection((h, int(p)), timeout=30)
        k = base64.b64encode(os.urandom(16)).decode()
        s.s.sendall(('GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\n'
                     'Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n'
                     'Sec-WebSocket-Version: 13\r\n\r\n' % (path, host, k))
                    .encode())
        b = b''
        while b'\r\n\r\n' not in b:
            b += s.s.recv(4096)
        s.buf = b.split(b'\r\n\r\n', 1)[1]
        s.n = 0

    def _j(s, p):
        h = bytearray([0x81])
        n = len(p)
        if n < 126:
            h.append(0x80 | n)
        elif n < 65536:
            h.append(0x80 | 126)
            h += struct.pack('>H', n)
        else:
            h.append(0x80 | 127)
            h += struct.pack('>Q', n)
        k = os.urandom(4)
        h += k
        s.s.sendall(bytes(h) + bytes(x ^ k[i % 4] for i, x in enumerate(p)))

    def _b(s):
        while len(s.buf) < 2:
            x = s.s.recv(65536)
            if not x:
                return None
            s.buf += x
        d = s.buf
        pl = d[1] & 0x7F
        g = 2
        if pl == 126:
            while len(d) < 4:
                d += s.s.recv(65536)
            pl = struct.unpack('>H', d[2:4])[0]
            g = 4
        elif pl == 127:
            while len(d) < 10:
                d += s.s.recv(65536)
            pl = struct.unpack('>Q', d[2:10])[0]
            g = 10
        while len(d) < g + pl:
            x = s.s.recv(65536)
            if not x:
                return None
            d += x
        out = d[g:g + pl]
        s.buf = d[g + pl:]
        try:
            return out.decode()
        except Exception:
            return None

    def cmd(s, m, p=None):
        s.n += 1
        i = s.n
        s._j(json.dumps({'id': i, 'method': m, 'params': p or {}}).encode())
        for _ in range(400):
            t = s._b()
            if t is None:
                return {}
            try:
                j = json.loads(t)
            except Exception:
                continue
            if j.get('id') == i:
                return j
        return {}

    def ev(s, expr):
        try:
            return (s.cmd('Runtime.evaluate',
                          {'expression': expr, 'returnByValue': True})
                    .get('result', {}).get('result', {}).get('value'))
        except Exception:
            return None


tok = subprocess.run(
    ['docker', 'exec', '-i', '-w', '/app', 'eduai-app', 'python3', '-'],
    input=("import sys;sys.path.insert(0,'/app')\n"
           "from app.auth import buat_token\nprint(buat_token(%d))" % USER).encode(),
    capture_output=True).stdout.decode().strip()

tab = http('/json/new?about:blank', metode='PUT')
ws = WS(tab['webSocketDebuggerUrl'])
ws.cmd('Page.enable')
ws.cmd('Network.clearBrowserCache')
ws.cmd('Network.enable')
ws.cmd('Network.setCookie', {'name': 'eduai_session', 'value': tok,
                             'domain': DOMAIN, 'path': '/',
                             'secure': True, 'httpOnly': True})
ws.cmd('Page.navigate', {'url': 'https://%s/edit/%d' % (DOMAIN, FID)})

JS = ("(()=>{const b=document.body.innerText||'';"
      "const f=document.querySelector('iframe');"
      "const g=document.getElementById('modal-galat');"
      "return JSON.stringify({"
      " iframe: !!f,"
      " masih_loading: b.includes('sedang disiapkan'),"
      " ada_minus4: b.includes('Unduhan gagal'),"
      " pesan: (b.match(/(Unduhan gagal[^\\n]{0,40}|Naskahmu[^\\n]{0,30})/)||[''])[0]"
      "});})()")

print('buka https://%s/edit/%d' % (DOMAIN, FID))
for dtk in range(15, 301, 15):
    time.sleep(15)
    st = ws.ev(JS)
    print('  dtk %3d: %s' % (dtk, st))
    if st and 'masih_loading":false' in st.replace(' ', ''):
        break

png = '/opt/data/services/eduai-publishing/_sketsa/editor-produksi.png'
r = ws.cmd('Page.captureScreenshot', {'format': 'png'})
if r.get('result', {}).get('data'):
    open(png, 'wb').write(base64.b64decode(r['result']['data']))
    print('PNG:', png, os.path.getsize(png), 'byte')
try:
    http('/json/close/' + tab['id'])
except Exception:
    pass
