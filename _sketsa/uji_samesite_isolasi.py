"""UJI TERISOLASI — apakah SameSite=Lax benar-benar penyebab cookie hilang?

TIDAK menyentuh produksi. Caranya: pasang DUA cookie di browser dengan nama
berbeda (keduanya domain produksi), satu Lax satu None, lalu lihat mana yang
benar-benar IKUT pada permintaan /oo/aset dari dalam iframe.

Kalau Lax hilang & None ikut => hipotesis TERBUKTI, patch layak dipasang.
"""
import base64
import json
import os
import socket
import struct
import subprocess
import time
import urllib.request

DOMAIN, FID = 'eduai.bikinaja.id', 9


def http(p, m=None):
    r = urllib.request.Request('http://127.0.0.1:9333' + p, method=m)
    with urllib.request.urlopen(r, timeout=10) as x:
        return json.loads(x.read().decode() or '{}')


class WS:
    def __init__(s, url):
        _, rest = url.split('://', 1)
        host, path = rest.split('/', 1)
        h, p = host.split(':')
        s.s = socket.create_connection((h, int(p)), timeout=25)
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
            except socket.timeout:
                return None
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
        for _ in range(900):
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


tok = subprocess.run(
    ['docker', 'exec', '-i', '-w', '/app', 'eduai-app', 'python3', '-'],
    input=("import sys;sys.path.insert(0,'/app')\n"
           "from app.auth import buat_token\nprint(buat_token(3))").encode(),
    capture_output=True).stdout.decode().strip()

tab = http('/json/new?about:blank', m='PUT')
ws = WS(tab['webSocketDebuggerUrl'])
ws.cmd('Page.enable')
ws.cmd('Runtime.enable')
ws.cmd('Network.enable')
ws.cmd('Network.clearBrowserCache')
ws.cmd('Network.clearBrowserCookies')

# DUA cookie uji, nama beda, atribut beda
r1 = ws.cmd('Network.setCookie', {'name': 'uji_lax', 'value': tok, 'domain': DOMAIN,
                                  'path': '/', 'secure': True, 'sameSite': 'Lax'})
r2 = ws.cmd('Network.setCookie', {'name': 'uji_none', 'value': tok, 'domain': DOMAIN,
                                  'path': '/', 'secure': True, 'sameSite': 'None'})
# cookie SESI juga: pasang TANPA httpOnly supaya Chrome menyimpannya
r3 = ws.cmd('Network.setCookie', {'name': 'eduai_session', 'value': tok,
                                  'domain': DOMAIN, 'path': '/',
                                  'secure': True, 'sameSite': 'Lax'})
print('set uji_lax  :', r1.get('result'))
print('set uji_none :', r2.get('result'))
print('set sesi     :', r3.get('result'))
ck = ws.cmd('Network.getCookies', {'urls': ['https://' + DOMAIN + '/']})
print('cookie terpasang:', [c['name'] for c in ck.get('result', {}).get('cookies', [])])

ws.s.settimeout(25)
ws.cmd('Page.navigate', {'url': 'https://%s/edit/%d' % (DOMAIN, FID)})

ketemu = {}
ada = []
t0 = time.time()
while time.time() - t0 < 150:
    r = ws._b()
    if r is None:
        break
    try:
        j = json.loads(r)
    except Exception:
        continue
    if j.get('method') == 'Network.requestWillBeSent':
        u = j['params']['request']['url']
        if '/oo/aset' in u:
            ada.append(u)
            ini = j['params'].get('initiator', {})
            asal = ini.get('url', '') or str(ini.get('type', ''))
            if 'asal' not in ketemu:
                ketemu['asal'] = []
            if len(ketemu['asal']) < 3:
                ketemu['asal'].append(asal[:80])
            ck = j['params']['request'].get('headers', {}).get('Cookie', '')
            if 'lax' not in ketemu:
                ketemu['lax'] = 'uji_lax' in ck
            if 'none' not in ketemu:
                ketemu['none'] = 'uji_none' in ck
            if 'sesi' not in ketemu:
                ketemu['sesi'] = 'eduai_session' in ck

print()
print('ASAL permintaan aset (initiator):')
for a in ketemu.get('asal', []):
    print('   ', a)
print()
print('URL sekarang   :', ws.ev('location.href'))
print('judul          :', ws.ev('document.title'))
print('iframe         :', ws.ev("document.querySelectorAll('iframe').length"))
print('loading tampil :', ws.ev("(function(){var m=document.getElementById('memuat');return m? !m.hidden : 'tak ada';})()"))
print('galat tampil   :', ws.ev("(function(){var g=document.getElementById('galat');return g? !g.hidden : 'tak ada';})()"))
print('galat pesan    :', ws.ev("(document.getElementById('galat-pesan')||{}).textContent"))
print()
print('jumlah permintaan /oo/aset terlihat:', len(ada))
for u in ada[:3]:
    print('   ', u[:96])
print('=== HASIL PADA PERMINTAAN /oo/aset DARI IFRAME ===')
print('  cookie uji_lax   (SameSite=Lax)  ikut?', ketemu.get('lax'))
print('  cookie uji_none  (SameSite=None) ikut?', ketemu.get('none'))
print('  cookie eduai_session             ikut?', ketemu.get('sesi'))
print()
if ketemu.get('none') and not ketemu.get('lax'):
    print('  ✅ TERBUKTI: SameSite=None IKUT, Lax TIDAK. Patch layak dipasang.')
elif ketemu.get('lax') and ketemu.get('none'):
    print('  ⚠️ DUA-DUANYA IKUT => hipotesis SALAH, cari sebab lain.')
elif not ketemu.get('lax') and not ketemu.get('none'):
    print('  ⚠️ DUA-DUANYA TIDAK IKUT => bukan soal sameSite.')
try:
    http('/json/close/' + tab['id'])
except Exception:
    pass
