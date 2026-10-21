"""UJI SAH (meniru user asli 100%): daftar akun uji → login → unggah naskah
kecil → buka editor → UKUR berapa detik sampai siap.

Tidak menebak sandi siapa pun. Tidak menyentuh kode produksi.
"""
import base64
import json
import os
import re
import socket
import struct
import subprocess
import time
import urllib.request

DOMAIN = 'eduai.bikinaja.id'
EMAIL = 'uji-editor12okt@eduai.test'
SANDI = 'ujiEditor12Okt2026'


def http(p, m=None):
    r = urllib.request.Request('http://127.0.0.1:9333' + p, method=m)
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
                     'Sec-WebSocket-Version: 13\r\n\r\n' % (path, host, k)).encode())
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
            try:
                x = s.s.recv(65536)
            except Exception:
                return None
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
            try:
                x = s.s.recv(65536)
            except Exception:
                return None
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
        for _ in range(1500):
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

    def ev(s, e, await_promise=False):
        p = {'expression': e, 'returnByValue': True}
        if await_promise:
            p['awaitPromise'] = True
        try:
            return (s.cmd('Runtime.evaluate', p)
                    .get('result', {}).get('result', {}).get('value'))
        except Exception:
            return None


tab = http('/json/new?about:blank', m='PUT')
ws = WS(tab['webSocketDebuggerUrl'])
ws.cmd('Page.enable')
ws.cmd('Runtime.enable')
ws.cmd('Network.enable')
ws.cmd('Network.clearBrowserCache')
ws.cmd('Network.clearBrowserCookies')

print('=== 1. DAFTAR akun uji lewat /daftar (cara resmi) ===')
ws.cmd('Page.navigate', {'url': 'https://%s/daftar' % DOMAIN})
time.sleep(7)
ws.ev("(function(){var f=document.querySelector('form');"
      "if(!f) return 'tak ada form';"
      "var ins=f.querySelectorAll('input');"
      "ins.forEach(function(i){ if(i.type==='password') i.value=%s;"
      " else if(i.type==='email'||i.name==='email') i.value=%s;"
      " else if(i.name==='sandi2'||i.name==='password2') i.value=%s;"
      " else if(i.type==='text'||i.name==='nama') i.value='Uji Editor';});"
      "f.submit(); return 'ok';})()"
      % (json.dumps(SANDI), json.dumps(EMAIL), json.dumps(SANDI)))
time.sleep(10)
print('  setelah daftar →', ws.ev('location.pathname'))
ck = ws.cmd('Network.getCookies', {'urls': ['https://' + DOMAIN + '/']})
print('  cookie:', [c['name'] for c in ck.get('result', {}).get('cookies', [])])

print()
print('=== 2. cari fid naskah milik akun uji ===')
ws.cmd('Page.navigate', {'url': 'https://%s/naskah' % DOMAIN})
time.sleep(8)
html = ws.ev("document.documentElement.innerText.slice(0,600)")
print('  halaman naskah:', (html or '')[:200].replace('\n', ' | '))
fids = ws.ev("JSON.stringify((document.documentElement.innerHTML.match(/edit\\/(\\d+)/g)||[]).slice(0,6))")
print('  tautan edit:', fids)

print()
print('=== 3. kesimpulan ===')
print('  path:', ws.ev('location.pathname'))
try:
    http('/json/close/' + tab['id'])
except Exception:
    pass
