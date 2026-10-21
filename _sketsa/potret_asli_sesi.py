"""Potret HALAMAN ASLI (bukan tiruan) — pakai cookie sesi yang disuntik.

Cara ini MEMBUKTIKAN tampilan sebenarnya: CSS asli, JS asli, data asli.
Ini yang benar; potret HTML tiruan sudah 4× menyesatkan Wulan (mata bilang
"CSS tidak terpakai" padahal itu cacat ALAT UKUR, bukan cacat aplikasi).

PAKAI: python3 _sketsa/potret_asli_sesi.py <URL> <keluar.png> [lebar] [tinggi]
"""
import base64, hashlib, json, os, socket, struct, subprocess, sys, time
import urllib.request

CDP = 'http://127.0.0.1:9333'


class Tab:
    def __init__(self, url, timeout=30):
        self.ws = None
        for _ in range(20):
            try:
                self.ws = socket.create_connection(('127.0.0.1', 9333), timeout=10)
                break
            except Exception:
                time.sleep(1)
        if not self.ws:
            raise RuntimeError('CDP tidak bisa disambung')
        req = urllib.request.Request(CDP + '/json/new?' + url, method='PUT')
        self.tab = json.loads(urllib.request.urlopen(req, timeout=10).read())
        self.url_ws = self.tab['webSocketDebuggerUrl'].replace('ws://', '')
        host, _, path = self.url_ws.partition('/')
        self.host = host; self.path = '/' + path
        self.ws = socket.create_connection((host.split(':')[0], int(host.split(':')[1])), timeout=timeout)
        self.kunci = base64.b64encode(os.urandom(16)).decode()
        tangan = (f'GET {self.path} HTTP/1.1\r\nHost: {host}\r\n'
                  f'Upgrade: websocket\r\nConnection: Upgrade\r\n'
                  f'Sec-WebSocket-Key: {self.kunci}\r\n'
                  f'Sec-WebSocket-Version: 13\r\n\r\n')
        self.ws.sendall(tangan.encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            buf += self.ws.recv(4096)
        if b'101' not in buf.split(b'\r\n')[0]:
            raise RuntimeError('Handshake GAGAL: ' + buf[:200].decode(errors='replace'))
        self.sisa = buf.split(b'\r\n\r\n', 1)[1]
        self.n = [0]

    def kirim(self, method, **par):
        self.n[0] += 1
        pesan = json.dumps({'id': self.n[0], 'method': method, 'params': par})
        data = pesan.encode()
        panjang = len(data)
        kepala = b'\x81'
        if panjang < 126:
            kepala += bytes([0x80 | panjang])
        elif panjang < 65536:
            kepala += bytes([0x80 | 126]) + struct.pack('>H', panjang)
        else:
            kepala += bytes([0x80 | 127]) + struct.pack('>Q', panjang)
        topeng = os.urandom(4)
        kepala += topeng
        data = bytes(b ^ topeng[i % 4] for i, b in enumerate(data))
        self.ws.sendall(kepala + data)

    def terima(self, tunggu=25):
        self.ws.settimeout(tunggu)
        akhir = time.time() + tunggu
        while time.time() < akhir:
            while True:
                if len(self.sisa) < 2:
                    break
                b1, b2 = self.sisa[0], self.sisa[1]
                panjang = b2 & 0x7F
                geser = 2
                if panjang == 126:
                    if len(self.sisa) < 4:
                        break
                    panjang = struct.unpack('>H', self.sisa[2:4])[0]; geser = 4
                elif panjang == 127:
                    if len(self.sisa) < 10:
                        break
                    panjang = struct.unpack('>Q', self.sisa[2:10])[0]; geser = 10
                if len(self.sisa) < geser + panjang:
                    break
                isi = self.sisa[geser:geser + panjang]
                self.sisa = self.sisa[geser + panjang:]
                try:
                    d = json.loads(isi)
                except Exception:
                    continue
                if 'id' in d and d['id'] == self.n[0]:
                    return d
            try:
                potong = self.ws.recv(65536)
            except socket.timeout:
                break
            if not potong:
                break
            self.sisa += potong
        return {}

    def tanya(self, method, **par):
        self.kirim(method, **par)
        return self.terima()


def main():
    if len(sys.argv) < 3:
        print(__doc__); return 2
    url, keluar = sys.argv[1], sys.argv[2]
    lebar = int(sys.argv[3]) if len(sys.argv) > 3 else 1180
    tinggi = int(sys.argv[4]) if len(sys.argv) > 4 else 1500

    #  ── token sesi dibuat fungsi app yang SAMA ──
    kode = ("from app.auth import buat_token\n"
            "from app.config import SESSION_COOKIE\n"
            "print(SESSION_COOKIE + '|' + buat_token(3))\n")
    r = subprocess.run(['docker', 'exec', '-w', '/app', 'eduai-app',
                        'python3', '-c', kode], capture_output=True, text=True,
                       timeout=90)
    if r.returncode != 0:
        print('token gagal:', r.stderr[-300:]); return 1
    nama_cookie, token = r.stdout.strip().split('|', 1)

    t = Tab('about:blank')
    t.tanya('Page.enable')
    t.tanya('Emulation.setDeviceMetricsOverride', width=lebar, height=tinggi,
            deviceScaleFactor=1, mobile=False)
    hasil = t.tanya('Network.setCookie', name=nama_cookie, value=token,
                    domain='eduai.bikinaja.id', path='/', secure=True,
                    httpOnly=True)
    print('cookie:', hasil.get('result', {}).get('success'))
    t.tanya('Page.navigate', url=url)
    time.sleep(9)
    t.tanya('Page.bringToFront')
    time.sleep(2)
    r2 = t.tanya('Page.captureScreenshot', format='png',
                 captureBeyondViewport=True)
    d = r2.get('result', {}).get('data')
    if not d:
        print('potret gagal:', json.dumps(r2)[:300]); return 1
    open(keluar, 'wb').write(base64.b64decode(d))
    print(f'✅ {keluar} — {os.path.getsize(keluar)} byte '
          f'· sha {hashlib.sha256(open(keluar,"rb").read()).hexdigest()[:12]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
