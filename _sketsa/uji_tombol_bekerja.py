"""UJI + POTRET: tombol "EduAi bantu isi" BEKERJA (13Okt26, setelah perbaikan JS).

Pakai alat RESMI yang sudah ada:
  - `_sketsa/potret_asli_sesi.py` (potret sesi asli, token dari fungsi app)
  - pola CDP mentah yang sama

Yang dibuktikan (bukan dibaca dari kode):
  isi judul → klik tombol → kata kunci muncul + chip tampil + pesan jujur.
"""
import base64
import hashlib
import json
import os
import socket
import struct
import subprocess
import sys
import time
import urllib.request

CDP = 'http://127.0.0.1:9333'


class Tab:
    """Sambungan CDP mentah (tanpa header Origin) — sama seperti alat resmi."""

    def __init__(self, url, timeout=30):
        self.ws = socket.create_connection(('127.0.0.1', 9333), timeout=10)
        kunci = base64.b64encode(os.urandom(16)).decode()
        jalur = url.split('://', 1)[1].split('/', 1)[1]
        req = (f'GET /{jalur} HTTP/1.1\r\nHost: 127.0.0.1:9333\r\n'
               f'Upgrade: websocket\r\nConnection: Upgrade\r\n'
               f'Sec-WebSocket-Key: {kunci}\r\nSec-WebSocket-Version: 13\r\n'
               f'\r\n').encode()
        self.ws.sendall(req)
        buf = b''
        while b'\r\n\r\n' not in buf:
            buf += self.ws.recv(4096)
        self.sisa = buf.split(b'\r\n\r\n', 1)[1]
        self.n = 0

    def _kirim(self, data):
        pjg = len(data)
        head = bytes([0x81])
        if pjg < 126:
            head += bytes([0x80 | pjg])
        elif pjg < 65536:
            head += bytes([0x80 | 126]) + struct.pack('>H', pjg)
        else:
            head += bytes([0x80 | 127]) + struct.pack('>Q', pjg)
        mask = os.urandom(4)
        isi = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        self.ws.sendall(head + mask + isi)

    def _baca(self):
        def baca(n):
            out = b''
            while len(out) < n:
                potong = self.ws.recv(n - len(out))
                if not potong:
                    raise ConnectionError('socket tutup')
                out += potong
            return out
        b1, b2 = baca(2)
        pjg = b2 & 0x7F
        if pjg == 126:
            pjg = struct.unpack('>H', baca(2))[0]
        elif pjg == 127:
            pjg = struct.unpack('>Q', baca(8))[0]
        return baca(pjg).decode('utf-8', 'ignore')

    def tanya(self, metode, **params):
        self.n += 1
        self._kirim(json.dumps({'id': self.n, 'method': metode,
                                'params': params}).encode())
        for _ in range(200):
            pesan = self._baca()
            try:
                d = json.loads(pesan)
            except Exception:                                         # noqa: BLE001
                continue
            if d.get('id') == self.n:
                return d
        return {}

    def tutup(self):
        try:
            self.ws.close()
        except Exception:                                             # noqa: BLE001
            pass


def buka_tab():
    req = urllib.request.Request(f'{CDP}/json/new?about:blank', method='PUT')
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception:                                                 # noqa: BLE001
        with urllib.request.urlopen(f'{CDP}/json/new?about:blank',
                                    timeout=10) as r:
            return json.loads(r.read())


# ── token sesi dari fungsi app yang SAMA ──
kode = ("from app.auth import buat_token\n"
        "from app.config import SESSION_COOKIE\n"
        "print(SESSION_COOKIE + '|' + buat_token(3))\n")
r = subprocess.run(['docker', 'exec', '-w', '/app', 'eduai-app',
                    'python3', '-c', kode], capture_output=True, text=True,
                   timeout=90)
if r.returncode != 0:
    print('token gagal:', r.stderr[-300:])
    sys.exit(1)
nama_cookie, token = r.stdout.strip().split('|', 1)
print('  ✅ token sesi dibuat')

ip = subprocess.run(['getent', 'hosts', 'eduai-app'],
                    capture_output=True, text=True).stdout.split()[0]
BASE = f'http://{ip}:8000'

info = buka_tab()
tid = info['id']
t = Tab(info['webSocketDebuggerUrl'])
try:
    t.tanya('Page.enable')
    t.tanya('Network.enable')
    t.tanya('Network.setCookie', name=nama_cookie, value=token,
            domain=ip, path='/', httpOnly=True)
    t.tanya('Emulation.setDeviceMetricsOverride', width=430, height=1000,
            deviceScaleFactor=2, mobile=True)
    t.tanya('Page.navigate', url=BASE + '/referensi')
    time.sleep(8)

    #  ── 1. Isi JUDUL (judul nyata yg tadi bikin masalah) ──
    t.tanya('Runtime.evaluate', expression=(
        "var i=document.getElementById('kk-ai');"
        "i.value='Pengaruh Keaslian Streamer dan Interaksi Parasosial "
        "terhadap Pembelian Impulsif pada Live Streaming Commerce';"
        "i.dispatchEvent(new Event('input',{bubbles:true})); 'SIAP'"),
        returnByValue=True)
    time.sleep(1)

    #  ── 2. KLIK tombol bantu ──
    k = t.tanya('Runtime.evaluate', expression=(
        "document.getElementById('btn-bantu').click(); 'DIKLIK'"),
        returnByValue=True)
    print('  klik:', k.get('result', {}).get('result', {}).get('value'))

    #  ── 3. Pantau HASIL (sampai 40 detik) ──
    akhir = {}
    for detik in range(1, 21):
        time.sleep(2)
        h = t.tanya('Runtime.evaluate', expression=(
            "JSON.stringify({"
            " nilai:(document.getElementById('kk-ai')||{}).value||'',"
            " pesan:(document.getElementById('pesan')||{}).innerText||'',"
            " chip:Array.from(document.querySelectorAll('#bantu-chip span'))"
            "      .map(function(c){return c.innerText.trim();}),"
            " info:(document.getElementById('bantu-info')||{}).innerText||''"
            "})"), returnByValue=True)
        v = h.get('result', {}).get('result', {}).get('value') or '{}'
        akhir = json.loads(v)
        print(f'    t={detik*2}s → nilai={akhir.get("nilai","")[:60]!r} '
              f'chip={akhir.get("chip")}')
        if akhir.get('pesan') or akhir.get('chip'):
            break

    #  ── 4. Potret ──
    t.tanya('Page.bringToFront')
    time.sleep(1)
    g = t.tanya('Page.captureScreenshot', format='png')
    d = g.get('result', {}).get('data')
    if d:
        keluar = '/opt/data/ref_ai_7_berhasil.png'
        raw = base64.b64decode(d)
        open(keluar, 'wb').write(raw)
        print(f'  ✅ {keluar} — {len(raw)} byte · sha '
              f'{hashlib.sha256(raw).hexdigest()[:12]}')
    else:
        print('  ❌ potret gagal:', json.dumps(g)[:200])

    print()
    print('═══ HASIL AKHIR (dibaca dari HALAMAN, bukan dikira) ═══')
    print('  kata kunci :', repr(akhir.get('nilai', ''))[:160])
    print('  chip       :', akhir.get('chip'))
    print('  keterangan :', repr(akhir.get('info', ''))[:120])
    print('  pesan      :', repr(akhir.get('pesan', ''))[:120])
finally:
    try:
        urllib.request.urlopen(f'{CDP}/json/close/{tid}', timeout=5).read()
    except Exception:                                                 # noqa: BLE001
        pass
    t.tutup()
