"""UJI EDITOR ONLYOFFICE — apakah modal "Unduhan gagal" (-4) masih muncul?
11Okt26. Bukti dari HALAMAN NYATA, bukan asumsi.

Jalankan dari host: python3 _sketsa/uji_editor_oo.py
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
USER = 3          # wulan@bikinaja.me (pemilik fid=9)
FID = 9           # TESIS_LENGKAP_Goras.docx
OUT = '/opt/data/services/eduai-publishing/_sketsa/editor-oo.png'


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
        s.s = socket.create_connection((u.hostname, u.port), timeout=40)
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
            while len(d) < 4:
                x = s.s.recv(4096)
                if not x:
                    return None
                d += x
            p = struct.unpack('>H', d[2:4])[0]
            g = 4
        elif p == 127:
            while len(d) < 10:
                x = s.s.recv(4096)
                if not x:
                    return None
                d += x
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
        for _ in range(80):
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
    input=("import sys;sys.path.insert(0,'/app')\n"
           "from app.auth import buat_token\nprint(buat_token(%d))" % USER).encode(),
    capture_output=True).stdout.decode().strip()
print('token user %d panjang: %d' % (USER, len(tok)))

tab = http('/json/new?about:blank', 'PUT')
ws = WS(tab['webSocketDebuggerUrl'])
ws.cmd('Page.enable')
ws.cmd('Network.enable')
# 12Okt26: BERSIHKAN CACHE **SEBELUM** pasang cookie. Tanpa ini OO memakai
# ulang SESI/DOKUMEN LAMA per document-key (jejak: WebSocket membuat sesi
# utk key LAMA walau HTML sudah kirim key BARU).
url = 'http://%s:8000/edit/%d' % (IP, FID)
print('buka:', url)
ws.cmd('Network.setCacheDisabled', {'cacheDisabled': True})
ws.cmd('Network.clearBrowserCache')
ws.cmd('Storage.clearDataForOrigin',
       {'origin': 'http://%s:8000' % IP, 'storageTypes': 'all'})
# ⚠️ cookie DIPASANG SESUDAH pembersihan — kalau sebelum, ikut terhapus
#    dan halaman jadi /masuk (GAGAL PALSU, pernah kejadian 12Okt26).
ws.cmd('Network.setCookie', {'name': 'eduai_session', 'value': tok,
                             'url': 'http://%s:8000/' % IP, 'path': '/',
                             'httpOnly': True})
ws.cmd('Emulation.setDeviceMetricsOverride',
       {'width': 1280, 'height': 900, 'deviceScaleFactor': 1, 'mobile': False})

# kumpulkan galat konsol + permintaan jaringan yang gagal
ws.cmd('Log.enable')
ws.cmd('Page.navigate', {'url': url})

print('menunggu editor (maks 60 dtk)...')
muncul_galat = None
for i in range(30):
    time.sleep(2)
    galat_tampil = ws.ev(
        "(() => { const g=document.getElementById('galat');"
        " return g ? (!g.hidden) : null; })()")
    pesan = ws.ev(
        "(() => { const p=document.getElementById('galat-pesan');"
        " return p ? p.textContent : null; })()")
    if galat_tampil:
        muncul_galat = pesan
        print('  ⚠️ MODAL GALAT muncul di detik %d: %r' % (i * 2, pesan))
        break
    if i % 3 == 0:
        print('  dtk %2d: modal tersembunyi · iframe OO ada=%s'
              % (i * 2, ws.ev("!!document.querySelector('iframe')")))
else:
    print('  60 dtk: modal galat TIDAK muncul')

# bukti tambahan: elemen editor OO benar-benar tumbuh?
info = ws.ev("""(() => {
  const f = document.querySelector('iframe');
  const r = f ? f.getBoundingClientRect() : null;
  return JSON.stringify({
    iframe: !!f, w: r ? Math.round(r.width) : 0, h: r ? Math.round(r.height) : 0,
    galat_hidden: (document.getElementById('galat')||{}).hidden,
    judul: document.title
  }); })()""")
print('INFO EDITOR:', info)

png = ws.cmd('Page.captureScreenshot', {'format': 'png'}).get('result', {}).get('data', '')
if png:
    with open(OUT, 'wb') as f:
        f.write(base64.b64decode(png))
    print('PNG:', OUT, os.path.getsize(OUT), 'byte')

http('/json/close/' + tab['id'])
print()
if muncul_galat:
    print('HASIL: MASIH GAGAL — modal -4 muncul: %r' % muncul_galat)
    sys.exit(1)
print('HASIL: editor terbuka TANPA modal galat')
sys.exit(0)
