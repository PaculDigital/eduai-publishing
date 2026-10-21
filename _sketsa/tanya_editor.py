"""TANYA LANGSUNG KE EDITOR: dari mana OO dapat skema https?

Buka editor, lalu tanya objek DocsAPI di dalam iframe apa URL
dokumen/aset yang ia pakai. Jalankan dari host.
"""
import base64
import json
import os
import socket
import struct
import subprocess
import time
import urllib.request

IP = '172.17.0.8'
FID = 9
USER = 3


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
        p = d[1] & 0x7F
        g = 2
        if p == 126:
            while len(d) < 4:
                d += s.s.recv(65536)
            p = struct.unpack('>H', d[2:4])[0]
            g = 4
        elif p == 127:
            while len(d) < 10:
                d += s.s.recv(65536)
            p = struct.unpack('>Q', d[2:10])[0]
            g = 10
        while len(d) < g + p:
            x = s.s.recv(65536)
            if not x:
                return None
            d += x
        pl = d[g:g + p]
        s.buf = d[g + p:]
        try:
            return pl.decode()
        except Exception:
            return None

    def cmd(s, m, p=None):
        s.n += 1
        i = s.n
        s._j(json.dumps({'id': i, 'method': m, 'params': p or {}}).encode())
        for _ in range(300):
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
        return (s.cmd('Runtime.evaluate',
                      {'expression': expr, 'returnByValue': True,
                       'awaitPromise': True})
                .get('result', {}).get('result', {}).get('value'))


tok = subprocess.run(
    ['docker', 'exec', '-i', '-w', '/app', 'eduai-app', 'python3', '-'],
    input=("import sys;sys.path.insert(0,'/app')\n"
           "from app.auth import buat_token\nprint(buat_token(%d))" % USER).encode(),
    capture_output=True).stdout.decode().strip()

tab = http('/json/new?about:blank', metode='PUT')
ws = WS(tab['webSocketDebuggerUrl'])
ws.cmd('Page.enable')
ws.cmd('Network.enable')
ws.cmd('Network.clearBrowserCache')
ws.cmd('Network.setCacheDisabled', {'cacheDisabled': True})
ws.cmd('Storage.clearDataForOrigin',
       {'origin': 'http://%s:8000' % IP, 'storageTypes': 'all'})
ws.cmd('Network.setCookie', {'name': 'eduai_session', 'value': tok,
                             'url': 'http://%s:8000/' % IP, 'path': '/',
                             'httpOnly': True})
url = 'http://%s:8000/edit/%d' % (IP, FID)
ws.cmd('Page.navigate', {'url': url})
print('buka', url, '— menunggu 40 dtk...')
time.sleep(40)
# pastikan kita evaluasi di konteks frame UTAMA
ws.cmd('Page.enable')
sisa = ws.cmd('Runtime.evaluate', {'expression': '1+1', 'returnByValue': True})
print('uji konteks (harus 2):', sisa.get('result', {}).get('result', {}).get('value'))

# tanya ke DALAM iframe OO: apa base URL yang dipakainya?
JS = (
    "(() => {"
    " const f = document.querySelector('iframe');"
    " if (!f) return 'TIDAK ADA IFRAME';"
    " let out = [];"
    " const cari = (w, tag) => {"
    "  try {"
    "   const d = w.document;"
    "   out.push(tag + ' base=' + d.baseURI);"
    "   const s = d.querySelectorAll('script[src],link[href]');"
    "   for (const e of s) {"
    "     const u = e.src || e.href;"
    "     if (u && (u.includes('cache/files') || u.includes('Editor.bin')))"
    "       out.push(tag + ' ASET=' + u);"
    "   }"
    "   const fr = d.querySelector('iframe');"
    "   if (fr && fr.contentWindow) cari(fr.contentWindow, tag + '>');"
    "  } catch (e) { out.push(tag + ' ERR ' + String(e).slice(0,60)); }"
    " };"
    " cari(f.contentWindow, 'OO');"
    " const g = document.getElementById('galat');"
    " out.push('modal_tampil=' + (g ? !g.hidden : null));"
    " return out.join(' | ').slice(0, 1500);"
    "})()"
)
hasil = ws.ev(JS)
print('TANYA KE EDITOR:')
print(hasil)
try:
    http('/json/close/' + tab['id'])
except Exception:
    pass
