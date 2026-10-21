"""POTRET KOTAK MUTU (#det-mutu) di /mulai — lewat CDP :9333.

Alur: buat token sesi resmi (app.auth.buat_token) → set cookie via CDP →
buka /mulai → jalankan alur petakan pada naskah fid=115 (RUSAK, biar kotak MUNCUL)
→ tunggu kotak tampil → potret → tutup tab.

Jalankan DARI HOST: python3 _sketsa/potret_mutu.py
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
CONTAINER = 'eduai-app'
FID = 115          # WULAN-PDF-RESMI = rusak_konversi (kotak mutu WAJIB muncul)
OUT = '/opt/data/services/eduai-publishing/_sketsa/potret-mutu.png'


def cdp_http(path, metode='GET'):
    req = urllib.request.Request(CDP + path, method=metode)
    with urllib.request.urlopen(req, timeout=20) as r:
        isi = r.read().decode().strip()
    if not isi:
        return {}
    try:
        return json.loads(isi)
    except json.JSONDecodeError:
        return {'_mentah': isi[:150]}


class WS:
    def __init__(self, url):
        u = urlparse(url)
        self.s = socket.create_connection((u.hostname, u.port), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((
            'GET %s HTTP/1.1\r\nHost: %s:%s\r\nUpgrade: websocket\r\n'
            'Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n'
            'Sec-WebSocket-Version: 13\r\n\r\n'
            % (u.path, u.hostname, u.port, key)).encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            buf += self.s.recv(4096)
        self.buf = buf.split(b'\r\n\r\n', 1)[1]
        self.n = 0

    def _kirim(self, teks):
        data = teks.encode()
        head = bytearray([0x81])
        n = len(data)
        if n < 126:
            head.append(0x80 | n)
        elif n < 65536:
            head.append(0x80 | 126)
            head += struct.pack('>H', n)
        else:
            head.append(0x80 | 127)
            head += struct.pack('>Q', n)
        mask = os.urandom(4)
        head += mask
        self.s.sendall(bytes(head) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _baca(self):
        if len(self.buf) < 2:
            potong = self.s.recv(4096)
            if not potong:
                return None
            self.buf += potong
        data = self.buf
        panjang = data[1] & 0x7F
        geser = 2
        if panjang == 126:
            panjang = struct.unpack('>H', data[2:4])[0]
            geser = 4
        elif panjang == 127:
            panjang = struct.unpack('>Q', data[2:10])[0]
            geser = 10
        sementara = data
        while len(sementara) < geser + panjang:
            tambah = self.s.recv(65536)
            if not tambah:
                return None
            sementara += tambah
        isi = sementara[geser:geser + panjang]
        self.buf = sementara[geser + panjang:]
        return isi.decode('utf-8', 'replace')

    def cmd(self, metode, params=None, tunggu=40):
        self.n += 1
        mid = self.n
        self._kirim(json.dumps({'id': mid, 'method': metode, 'params': params or {}}))
        for _ in range(tunggu):
            teks = self._baca()
            if teks is None:
                return {}
            try:
                j = json.loads(teks)
            except Exception:
                continue
            if 'id' in j and j['id'] == mid:
                return j
        return {}

    def eval(self, expr, tunggu=40):
        j = self.cmd('Runtime.evaluate',
                     {'expression': expr, 'returnByValue': True, 'awaitPromise': True},
                     tunggu=tunggu)
        return j.get('result', {}).get('result', {}).get('value')


def docker_py(kode):
    """Jalankan python di dalam container, balas stdout."""
    p = subprocess.run(['docker', 'exec', '-i', '-w', '/app', CONTAINER,
                        'python3', '-'], input=kode.encode(),
                       capture_output=True)
    return p.stdout.decode('utf-8', 'replace').strip(), p.stderr.decode('utf-8', 'replace').strip()


print('== 1. BUAT TOKEN SESI UNTUK USER 8 (Asih, pemilik fid=115) ==')
kode = """
import sys
sys.path.insert(0, '/app')
from app.auth import buat_token
print(buat_token(8))
"""
token, err = docker_py(kode)
if not token or 'Traceback' in token or 'Error' in token:
    print('GAGAL bikin token:', token[:200], err[:300])
    sys.exit(1)
print('token panjang:', len(token))

print('== 2. BUKA TAB BARU + SET COOKIE ==')
tab = cdp_http('/json/new?about:blank', 'PUT')
ws = WS(tab['webSocketDebuggerUrl'])
ws.cmd('Page.enable')
ws.cmd('Network.enable')
IP = '172.17.0.8'
r = ws.cmd('Network.setCookie', {
    'name': 'eduai_session', 'value': token,
    'url': 'http://%s:8000/' % IP, 'path': '/', 'httpOnly': True,
})
print('setCookie:', json.dumps(r.get('result', {}), ensure_ascii=False)[:120])

print('== 3. BUKA /mulai (harus 200 halaman asli, bukan Masuk) ==')
ws.cmd('Page.navigate', {'url': 'http://%s:8000/mulai' % IP})
time.sleep(4)
judul = ws.eval('document.title')
print('judul:', repr(judul))
ada_kotak = ws.eval("!!document.getElementById('det-mutu')")
print('kotak #det-mutu ADA di DOM:', ada_kotak)

if not ada_kotak:
    print('GAGAL: kotak mutu tidak ada di halaman (mungkin ke halaman Masuk)')
    cdp_http('/json/close/' + tab['id'])
    sys.exit(1)

print('== 4. JALANKAN ALUR ASLI APP (deteksiBerkas) — BUKAN fetch mentah ==')
# ⚠️ JEBAKAN: `fetch` langsung hanya mengembalikan data; JS tampilan
#    (tampilMutu) TIDAK jalan ⇒ kotak tetap "—" ⇒ mudah dikira fitur rusak.
#    Uji tampilan WAJIB lewat fungsi asli app.
hasil = ws.eval("""
(async () => {
  try {
    if (typeof deteksiBerkas !== 'function') return 'FUNGSI deteksiBerkas TIDAK ADA';
    await deteksiBerkas(%d);
    return 'deteksiBerkas SIAP';
  } catch (e) { return 'GALAT: ' + e.message; }
})()
""" % FID, tunggu=180)
print('panggil deteksiBerkas:', hasil)

print('== 5. TUNGGU KOTAK MUNCUL + ISI ==')
for i in range(30):
    time.sleep(1)
    tampil = ws.eval("(() => { const k=document.getElementById('det-mutu'); return k ? (!k.classList.contains('sembunyi')) : false; })()")
    if tampil:
        print('kotak TAMPIL setelah %d dtk' % (i + 1))
        break
else:
    print('kotak belum tampil — paksa tampilkan untuk potret')
    ws.eval("document.getElementById('det-mutu').classList.remove('sembunyi')")

isi = ws.eval("(() => { const k=document.getElementById('det-mutu'); return k ? k.innerText : '(tidak ada)'; })()")
print('ISI KOTAK:', repr(isi))
warna = ws.eval("""(() => { const k=document.getElementById('det-mutu');
  const s=getComputedStyle(k);
  return JSON.stringify({bg:s.backgroundColor, warna:s.color, radius:s.borderRadius,
                         border:s.borderColor, lebar:k.getBoundingClientRect().width}); })()""")
print('GAYA:', warna)

print('== 6. POTRET ==')
ws.cmd('Emulation.setDeviceMetricsOverride',
       {'width': 1100, 'height': 1500, 'deviceScaleFactor': 1, 'mobile': False})
png = ws.cmd('Page.captureScreenshot', {'format': 'png'}).get('result', {}).get('data', '')
if png:
    with open(OUT, 'wb') as f:
        f.write(base64.b64decode(png))
    print('PNG:', OUT, os.path.getsize(OUT), 'byte')
else:
    print('PNG GAGAL')

cdp_http('/json/close/' + tab['id'])
print('TAB DITUTUP')
print()
print('HASIL:', 'LULUS' if (png and ada_kotak) else 'GAGAL')
sys.exit(0 if (png and ada_kotak) else 1)
