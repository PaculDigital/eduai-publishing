"""UJI SAH lanjutan: login sungguhan → UNGGAH naskah kecil → buka editor →
UKUR berapa detik sampai editor siap. Meniru user asli 100%.
"""
import base64
import json
import os
import socket
import struct
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

    def ev(s, e, ap=False):
        p = {'expression': e, 'returnByValue': True}
        if ap:
            p['awaitPromise'] = True
        try:
            return (s.cmd('Runtime.evaluate', p)
                    .get('result', {}).get('result', {}).get('value'))
        except Exception:
            return None


# --- siapkan naskah docx kecil untuk diunggah (dari berkas yg ada) ---
SRC = '/opt/data/services/eduai-publishing/_sketsa/naskah_uji_kecil.docx'
if not os.path.exists(SRC):
    import zipfile
    isi = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
           '<w:body><w:p><w:r><w:t>Naskah uji editor EduAi. '
           'Baris kedua untuk menguji memuat naskah kecil.</w:t></w:r></w:p>'
           '</w:body></w:document>')
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
          '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')
    with zipfile.ZipFile(SRC, 'w') as z:
        z.writestr('[Content_Types].xml', ct)
        z.writestr('_rels/.rels', rels)
        z.writestr('word/document.xml', isi)
    print('naskah uji dibuat:', SRC, os.path.getsize(SRC), 'byte')

b64 = base64.b64encode(open(SRC, 'rb').read()).decode()

tab = http('/json/new?about:blank', m='PUT')
ws = WS(tab['webSocketDebuggerUrl'])
ws.cmd('Page.enable')
ws.cmd('Runtime.enable')
ws.cmd('Network.enable')
ws.cmd('Network.clearBrowserCache')
ws.cmd('Network.clearBrowserCookies')

print('=== 1. login sungguhan ===')
ws.cmd('Page.navigate', {'url': 'https://%s/masuk' % DOMAIN})
time.sleep(7)
ws.ev("(function(){var f=document.querySelector('form');if(!f)return 'x';"
      "f.querySelectorAll('input').forEach(function(i){"
      "if(i.type==='password')i.value=%s;else i.value=%s;});f.submit();return 'ok';})()"
      % (json.dumps(SANDI), json.dumps(EMAIL)))
time.sleep(9)
p1 = ws.ev('location.pathname')
print('  path setelah login:', p1)
if p1 and 'masuk' in str(p1):
    print('  login gagal -> coba DAFTAR akun baru')
    ws.cmd('Page.navigate', {'url': 'https://%s/daftar' % DOMAIN})
    time.sleep(7)
    ws.ev("(function(){var f=document.querySelector('form');if(!f)return 'x';"
          "f.querySelectorAll('input').forEach(function(i){"
          "if(i.type==='password')i.value=%s;"
          "else if(i.type==='email'||i.name==='email')i.value=%s;"
          "else if(i.name==='sandi2'||i.name==='password2')i.value=%s;});"
          "f.submit();return 'ok';})()"
          % (json.dumps(SANDI), json.dumps(EMAIL), json.dumps(SANDI)))
    time.sleep(10)
    print('  path setelah daftar:', ws.ev('location.pathname'))

print()
print('=== 2. unggah naskah lewat halaman /naskah ===')
ws.cmd('Page.navigate', {'url': 'https://%s/naskah' % DOMAIN})
time.sleep(8)
ada_input = ws.ev("document.querySelectorAll('input[type=file]').length")
print('  input file:', ada_input)
if ada_input:
    ws.cmd('DOM.enable')
    doc = ws.cmd('DOM.getDocument', {'depth': -1})
    node = ws.cmd('DOM.querySelector', {'nodeId': doc['result']['root']['nodeId'],
                                        'selector': 'input[type=file]'})
    ws.cmd('DOM.setFileInputFiles', {'files': [SRC],
                                     'nodeId': node['result']['nodeId']})
    time.sleep(12)
print('  path setelah unggah:', ws.ev('location.pathname'))
fid = ws.ev("(function(){var m=location.href.match(/edit\\/(\\d+)/);"
            "if(m) return m[1];"
            "var a=document.querySelector('a[href*=\"/edit/\"]');"
            "return a? a.getAttribute('href') : 'belum ada';})()")
print('  tautan editor mentah:', fid)
import re as _re
_m = _re.search(r'(\d+)', str(fid))
fid = _m.group(1) if _m else None
print('  fid bersih:', fid)

print()
print('=== 3. UKUR: buka editor, hitung detik ===')
if fid and str(fid).isdigit():
    t0 = time.time()
    ws.cmd('Page.navigate', {'url': 'https://%s/edit/%s' % (DOMAIN, fid)})
    hasil = None
    while time.time() - t0 < 240:
        try:
            st = ws.ev("(function(){var m=document.getElementById('memuat');"
                       "return JSON.stringify({loading: m? !m.hidden : null,"
                       "galat: (document.getElementById('galat')||{}).hidden===false});})()")
            j = json.loads(st) if st else {}
        except Exception:
            j = {}
        if j.get('loading') is False or j.get('galat'):
            hasil = (time.time() - t0, j)
            break
        if int(time.time() - t0) % 20 < 5:
            print('   ...%.0f dtk' % (time.time() - t0))
        time.sleep(4)
    print()
    if hasil:
        print('  ✅ EDITOR SIAP dalam %.1f detik  %s' % hasil)
    else:
        print('  ❌ MASIH LOADING setelah 240 detik')
    print('  iframe         :', ws.ev("document.querySelectorAll('iframe').length"))
    print('  judul          :', ws.ev('document.title'))
    print('  galat pesan    :', ws.ev("(document.getElementById('galat-pesan')||{}).textContent"))
else:
    print('  fid tidak ditemukan — perlu lihat halaman /naskah manual')
try:
    http('/json/close/' + tab['id'])
except Exception:
    pass
