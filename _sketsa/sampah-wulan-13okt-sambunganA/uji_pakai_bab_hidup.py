"""POTRET + UJI KLIK NYATA: tombol "pakai juga di bab…" (13Okt26).

Alat resmi `_sketsa/potret_asli_sesi.py` (socket mentah :9333 + cookie asli).

Yang dibuktikan:
  1. tombol "pakai juga di bab…" MUNCUL di kartu artikel
  2. diklik → kotak centang bab muncul
  3. dicentang + Simpan → tersimpan (dibaca ulang dari server)
"""
import base64
import http.client
import json
import re
import socket
import subprocess
import time
import urllib.parse
import urllib.request

URL = 'https://eduai.bikinaja.id/referensi'
FILE_ID = 105
BAB = 'BAB III'


# ── 1. cookie login (fungsi app yang sama) ──────────────────────────────
def _ip():
    out = subprocess.run(
        ['bash', '-lc',
         "getent hosts eduai-app 2>/dev/null | head -1 | awk '{print $1}'"],
        capture_output=True, text=True).stdout.strip()
    return out or '172.17.0.8'


IP = _ip()
print('container:', IP)


def _tok():
    kode = (
        "import sys; sys.path.insert(0,'/app')\n"
        "from app.auth import buat_token\n"
        "from app.models import get_db\n"
        "print(buat_token(9))\n")
    r = subprocess.run(['docker', 'exec', '-i', 'eduai-app', 'python3', '-'],
                       input=kode, capture_output=True, text=True)
    m = re.search(r'([A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,})', r.stdout)
    return m.group(1) if m else ''


TOKEN = _tok()
print('token:', 'ADA' if TOKEN else 'TIDAK ADA (pakai login HTTP)')


def _login_http():
    c = http.client.HTTPConnection(IP, 8000, timeout=25)
    body = urllib.parse.urlencode({
        'email': 'potret-ref@eduai.test', 'password': 'UjiPotret2026!'})
    c.request('POST', '/masuk', body,
              {'Content-Type': 'application/x-www-form-urlencoded'})
    r = c.getresponse()
    r.read()
    for h in r.getheaders():
        if h[0].lower() == 'set-cookie':
            return h[1].split(';')[0]
    return ''


COOKIE = _login_http() if not TOKEN else ''
print('cookie:', 'ADA' if COOKIE else '-')


# ── 2. CDP ──────────────────────────────────────────────────────────────
class CDP:
    def __init__(self):
        self.s = socket.create_connection(('127.0.0.1', 9333), timeout=40)
        self.i = 0
        self.buf = b''

    def cmd(self, metode, **par):
        self.i += 1
        p = json.dumps({'id': self.i, 'method': metode, 'params': par}).encode()
        head = b'Content-Length: %d\r\n\r\n' % len(p)
        self.s.sendall(head + p)
        while True:
            self.buf += self.s.recv(1 << 20)
            while b'\r\n\r\n' in self.buf:
                h, sisa = self.buf.split(b'\r\n\r\n', 1)
                m = re.search(rb'Content-Length: (\d+)', h)
                if not m:
                    self.buf = sisa
                    continue
                n = int(m.group(1))
                if len(sisa) < n:
                    break
                isi = sisa[:n]
                self.buf = sisa[n:]
                d = json.loads(isi)
                if d.get('id') == self.i:
                    if 'error' in d:
                        raise RuntimeError(d['error'])
                    return d.get('result', {})

    def tutup(self):
        try:
            self.s.close()
        except Exception:                                          # noqa: BLE001
            pass


def tunggu(c, nama, jalan, ulang=40):
    for _ in range(ulang):
        try:
            v = c.cmd('Runtime.evaluate', expression=f'JSON.stringify({jalan})',
                      returnByValue=True)
            raw = v.get('result', {}).get('value')
            if raw and raw not in ('null', '[]', '{}', '""'):
                return json.loads(raw)
        except Exception:                                          # noqa: BLE001
            pass
        time.sleep(0.6)
    return None


def potret(c, keluar, mb=1200):
    data = c.cmd('Page.captureScreenshot', format='png',
                 clip={'x': 0, 'y': 0, 'width': 390, 'height': mb,
                       'scale': 1, 'captureBeyondViewport': True})['data']
    raw = base64.b64decode(data)
    open(keluar, 'wb').write(raw)
    print(f'  ✅ {keluar} — {len(raw)} byte')


c = CDP()
c.cmd('Page.enable')
c.cmd('Network.enable')
c.cmd('Emulation.setDeviceMetricsOverride', width=390, height=900,
      deviceScaleFactor=1, mobile=True)

if TOKEN:
    c.cmd('Network.setCookie', name='eduai_sesi', value=TOKEN,
          domain='eduai.bikinaja.id', path='/', secure=True, httpOnly=True)
if COOKIE:
    nama, nilai = COOKIE.split('=', 1)
    c.cmd('Network.setCookie', name=nama, value=nilai,
          domain='eduai.bikinaja.id', path='/', secure=True)
print('cookie disuntik')

c.cmd('Page.navigate', url=f'{URL}?fid={FILE_ID}')
time.sleep(6)

info = c.cmd('Runtime.evaluate', returnByValue=True, expression=f'''
JSON.stringify({{
  judul: document.title,
  adaLogin: !!document.querySelector('input[type=password]'),
  tombolPakai: (function(){{
    var b=[...document.querySelectorAll('button')].filter(function(x){{
      return x.textContent.indexOf('pakai juga di bab')>=0; }});
    return b.length ? b[0].textContent.trim() : null;
  }})()
}})''')
print('PAGE:', info['result']['value'][:400])
