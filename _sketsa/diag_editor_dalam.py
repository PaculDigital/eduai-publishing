"""DIAGNOSA DALAM BROWSER: apa yang OO laporkan saat gagal -4?

Bukti LANGSUNG dari editor yang hidup (bukan dari log server).
Jalankan dari host: python3 _sketsa/diag_editor_dalam.py
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
OUT = '_sketsa/diag-editor.png'

JS_KEADAAN = (
    "(() => {"
    " const f = document.querySelector('iframe');"
    " let dalam = null, err = null;"
    " try {"
    "  const w = f.contentWindow;"
    "  dalam = {judul: w.document.title,"
    "           teks: (w.document.body ? w.document.body.innerText.slice(0,200) : null)};"
    " } catch (e) { err = String(e).slice(0,120); }"
    " const g = document.getElementById('galat');"
    " const p = document.getElementById('galat-pesan');"
    " return JSON.stringify({punya_iframe: !!f,"
    "   src: f ? f.src.slice(0,150) : null,"
    "   lintas_origin: err, dalam: dalam,"
    "   galat_tampil: g ? !g.hidden : null,"
    "   galat_pesan: p ? p.textContent : null});"
    "})()"
)



JS_ASET = (
    "(() => {"
    " const f = document.querySelector('iframe');"
    " if (!f) return 'TIDAK ADA IFRAME';"
    " const out = [];"
    " try {"
    "  const d = f.contentWindow.document;"
    "  out.push('baseURI=' + d.baseURI);"
    "  for (const e of d.querySelectorAll('script[src],link[href]')) {"
    "   const u = e.src || e.href;"
    "   if (u && (u.includes('cache/files') || u.includes('Editor.bin')))"
    "     out.push('ASET=' + u);"
    "  }"
    "  const fr = d.querySelector('iframe#frameEditor');"
    "  if (fr && fr.contentWindow) {"
    "   out.push('frame.baseURI=' + fr.contentWindow.document.baseURI);"
    "   for (const s2 of fr.contentWindow.document.querySelectorAll('script[src]')) {"
    "    if (s2.src && s2.src.includes('cache')) out.push('frame ASET=' + s2.src);"
    "   }"
    "  }"
    " } catch (e) { out.push('ERR ' + String(e).slice(0,80)); }"
    " return out.join(' | ').slice(0,1200);"
    "})()"
)



JS_PERF = (
    "(() => {"
    " const out = [];"
    " const scan = (w,tag) => {"
    "  try { for (const e of w.performance.getEntriesByType('resource')) {"
    "   if (e.name.includes('Editor.bin') || e.name.includes('cache/files'))"
    "     out.push(tag + ' ' + e.name.slice(0,300));"
    "  } } catch(err) {}"
    " };"
    " scan(window,'LUAR');"
    " const f = document.querySelector('iframe');"
    " if (f) scan(f.contentWindow,'OO');"
    " return out.join(' || ').slice(0,1500) || 'TIDAK ADA entri Editor.bin';"
    "})()"
)


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
        s.log = []

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
            if j.get('method') in ('Log.entryAdded',
                                   'Runtime.consoleAPICalled',
                                   'Network.loadingFailed'):
                s.log.append(json.dumps(j)[:350])
            if j.get('id') == i:
                return j
        return {}

    def ev(s, expr):
        return (s.cmd('Runtime.evaluate',
                      {'expression': expr, 'returnByValue': True})
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
ws.cmd('Log.enable')
ws.cmd('Runtime.enable')
url = 'http://%s:8000/edit/%d' % (IP, FID)
ws.cmd('Network.clearBrowserCache')
ws.cmd('Network.setCacheDisabled', {'cacheDisabled': True})
ws.cmd('Storage.clearDataForOrigin',
       {'origin': 'http://%s:8000' % IP, 'storageTypes': 'all'})
ws.cmd('Network.setCookie', {'name': 'eduai_session', 'value': tok,
                             'url': 'http://%s:8000/' % IP, 'path': '/',
                             'httpOnly': True})
ws.cmd('Page.navigate', {'url': url})

print('menunggu 50 dtk lalu periksa keadaan editor...')
time.sleep(50)

keadaan = None
for _ in range(6):
    keadaan = ws.ev(JS_KEADAAN)
    if keadaan:
        break
    time.sleep(2)
print('KEADAAN:', keadaan)

print()
print('TANYA DALAM EDITOR:', ws.ev(JS_ASET))
print('URL ASET LENGKAP:', ws.ev(JS_PERF))
print()
print('=== PESAN KONSOL / NETWORK YANG GAGAL ===')
for b in ws.log[-25:]:
    print(' ', b[:300])

png = ws.cmd('Page.captureScreenshot', {'format': 'png'})
data = png.get('result', {}).get('data', '')
if data:
    with open(OUT, 'wb') as f:
        f.write(base64.b64decode(data))
    print('PNG:', OUT, os.path.getsize(OUT))
try:
    http('/json/close/' + tab['id'])
except Exception:
    pass
