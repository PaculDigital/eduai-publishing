"""UJI SAH: login SUNGGUHAN lewat /masuk di browser (meniru user asli),
lalu ukur: (1) apakah /edit/9 tetap terbuka? (2) aset bawa cookie?
(3) berapa detik sampai editor siap?

Akun uji DIBUAT BARU lewat /daftar (cara resmi, sama spt skrip uji lain),
supaya tidak menyentuh user produksi yang ada.
"""
import base64
import json
import os
import socket
import struct
import time
import urllib.parse
import urllib.request

DOMAIN = 'eduai.bikinaja.id'
EMAIL = 'potret-ref@eduai.test'   # user 9 — punya fid 105 (naskah kecil)
SANDI = 'ujiEditor12Okt2026'   # kalau gagal -> daftar baru


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
        for _ in range(1200):
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

    def ev(s, e):
        try:
            return (s.cmd('Runtime.evaluate',
                          {'expression': e, 'returnByValue': True})
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

# ---- 1. LOGIN SUNGGUHAN lewat /masuk (isi form, klik) ----
ws.cmd('Page.navigate', {'url': 'https://%s/masuk' % DOMAIN})
time.sleep(6)
ws.ev("(function(){var f=document.querySelector('form');"
      "if(!f) return 'tak ada form';"
      "document.querySelectorAll('input').forEach(function(i){"
      "i.value = (i.type==='password') ? %s : %s;});"
      "f.submit(); return 'dikirim';})()"
      % (json.dumps(SANDI), json.dumps(EMAIL)))
time.sleep(9)
print('setelah login →', ws.ev('location.pathname'))
ck = ws.cmd('Network.getCookies', {'urls': ['https://' + DOMAIN + '/']})
print('cookie di browser:', [c['name'] for c in
                             ck.get('result', {}).get('cookies', [])])

# ---- 2. buka editor, ukur ----
t0 = time.time()
ws.cmd('Page.navigate', {'url': 'https://%s/edit/105' % DOMAIN})
aset = []
tunggu = {}
while time.time() - t0 < 200:
    try:
        st = ws.ev("(function(){var m=document.getElementById('memuat');"
                   "return JSON.stringify({loading: m? !m.hidden : null,"
                   "galat: (document.getElementById('galat')||{}).hidden===false,"
                   "path: location.pathname});})()")
        j = json.loads(st) if st else {}
    except Exception:
        j = {}
    if j.get('path') not in ('/edit/105', None) and 'edit' not in str(j.get('path','')):
        tunggu = {'dilempar': j.get('path')}
        break
    if j.get('loading') is False or j.get('galat'):
        tunggu = j
        break
    time.sleep(4)
dt = time.time() - t0
print()
print('=== HASIL ===')
print('  path akhir     :', ws.ev('location.pathname'))
print('  judul          :', ws.ev('document.title'))
print('  iframe         :', ws.ev("document.querySelectorAll('iframe').length"))
print('  loading tampil :', ws.ev("(function(){var m=document.getElementById('memuat');return m? !m.hidden:'-';})()"))
print('  galat tampil   :', ws.ev("(function(){var g=document.getElementById('galat');return g? !g.hidden:'-';})()"))
print('  galat pesan    :', ws.ev("(document.getElementById('galat-pesan')||{}).textContent"))
print('  waktu tunggu   : %.1f dtk' % dt)
print('  kondisi akhir  :', tunggu)
try:
    http('/json/close/' + tab['id'])
except Exception:
    pass
