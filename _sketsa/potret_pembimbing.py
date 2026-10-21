#!/usr/bin/env python3
"""POTRET DASHBOARD PEMBIMBING (standar 25Sep26).

Menjawab: apakah pembimbing MELIHAT hasil revisi mahasiswa dengan jelas?

ALAT : _sketsa/potret_cdp.py (socket mentah · CDP :9333)
DATA : pembimbingan 80 "Prof. Uji Bab" (8 catatan) · 84 "Uji Sorotan 3.1" (1)
URL  : /tinjau/<token_sidik>  (tanpa login — pakai token)
"""
import base64
import json
import os
import socket
import sqlite3
import subprocess
import time
import urllib.request

BASE = 'https://eduai.bikinaja.id'
CDP = 'http://127.0.0.1:9333'
KELUAR = '/opt/data/services/eduai-publishing/_sketsa/bukti_sinkron'
os.makedirs(KELUAR, exist_ok=True)

#  ── ambil token dari container ──────────────────────────────────────────
def tok(pembimbingan_id: int) -> str:
    kode = (
        'import sqlite3;'
        'c=sqlite3.connect("/app/data/eduai.db");'
        f'print(c.execute("SELECT token_sidik FROM pembimbingan WHERE id={pembimbingan_id}")'
        '.fetchone()[0])'
    )
    r = subprocess.run(['docker', 'exec', 'eduai-app', 'python3', '-c', kode],
                       capture_output=True, text=True, timeout=60)
    return r.stdout.strip()


T80 = 'sjGg7kYVQozl4y9p-WvSouU-fk-jBQo-hPaDJhjsCjg'   # pembimbingan 85 (BARU, token mentah)
T84 = tok(84)
print(f'token mentah 85: {T80[:16]}…')


class Tab:
    def __init__(self, lebar=1500, tinggi=1200):
        req = urllib.request.Request(f'{CDP}/json/new?about:blank', method='PUT')
        try:
            tab = json.loads(urllib.request.urlopen(req, timeout=15).read())
        except Exception:                                                 # noqa: BLE001
            tab = json.loads(urllib.request.urlopen(
                f'{CDP}/json/new?about:blank', timeout=15).read())
        self.tid = tab['id']
        ws = tab['webSocketDebuggerUrl']
        hostport, path = ws.split('://', 1)[1].split('/', 1)
        self.s = socket.create_connection(
            (hostport.split(':')[0], int(hostport.split(':')[1])), timeout=60)
        kunci = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((
            f'GET /{path} HTTP/1.1\r\nHost: {hostport}\r\n'
            'Upgrade: websocket\r\nConnection: Upgrade\r\n'
            f'Sec-WebSocket-Key: {kunci}\r\nSec-WebSocket-Version: 13\r\n\r\n'
        ).encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            buf += self.s.recv(4096)
        self._id = 0
        self.lebar, self.tinggi = lebar, tinggi

    def _kr(self, metode, params):
        self._id += 1
        data = json.dumps({'id': self._id, 'method': metode,
                           'params': params or {}}).encode()
        mask = os.urandom(4)
        top = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        if len(data) < 126:
            hdr = bytes([0x81, 0x80 | len(data)])
        else:
            hdr = bytes([0x81, 0x80 | 126]) + len(data).to_bytes(2, 'big')
        self.s.sendall(hdr + mask + top)
        return self._id

    def _tr(self):
        h = self.s.recv(2)
        if not h:
            return None
        n = h[1] & 0x7F
        if n == 126:
            n = int.from_bytes(self.s.recv(2), 'big')
        elif n == 127:
            n = int.from_bytes(self.s.recv(8), 'big')
        d = b''
        while len(d) < n:
            d += self.s.recv(n - len(d))
        return json.loads(d)

    def cmd(self, metode, params=None, tunggu=60):
        pid = self._kr(metode, params)
        for _ in range(300):
            m = self._tr()
            if m is None:
                return None
            if m.get('id') == pid:
                return m
        return None

    def ke(self, url, tunggu=8):
        self.cmd('Page.enable')
        self.cmd('Page.navigate', {'url': url})
        time.sleep(tunggu)
        self.cmd('Emulation.setDeviceMetricsOverride', {
            'width': self.lebar, 'height': self.tinggi, 'deviceScaleFactor': 1,
            'mobile': False})
        time.sleep(1.5)

    def js(self, expr):
        r = self.cmd('Runtime.evaluate', {
            'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        try:
            return r['result']['result'].get('value')
        except Exception:                                                 # noqa: BLE001
            return None

    def potret(self, nama):
        r = self.cmd('Page.captureScreenshot', {'format': 'png'})
        if not (r and r.get('result', {}).get('data')):
            print(f'  ❌ {nama} — gagal')
            return None
        jalur = os.path.join(KELUAR, nama)
        with open(jalur, 'wb') as f:
            f.write(base64.b64decode(r['result']['data']))
        u = os.path.getsize(jalur)
        print(f'  {"✅" if u > 10000 else "⚠️"} {nama} — {u} byte')
        return jalur

    def tutup(self):
        try:
            self.s.close()
        except Exception:                                                 # noqa: BLE001
            pass
        try:
            urllib.request.urlopen(f'{CDP}/json/close/{self.tid}', timeout=10).read()
        except Exception:                                                 # noqa: BLE001
            pass


HALAMAN = [
    ('pmb-01-tinjau.png', f'{BASE}/tinjau/{T80}', 1500, 1200,
     'Dashboard pembimbing "Prof. Uji Mata" — lihat hasil revisi'),
    ('pmb-02-tinjau-84.png', f'{BASE}/tinjau/{T84}', 1500, 1100,
     'Dashboard pembimbing "Uji Sorotan 3.1" — 1 sorotan'),
]

if __name__ == '__main__':
    print('═' * 74)
    print('  POTRET DASHBOARD PEMBIMBING — STANDAR 25Sep26')
    print('═' * 74)
    for nama, url, lb, tg, ket in HALAMAN:
        print(f'\n▶ {ket}')
        t = Tab(lb, tg)
        try:
            t.ke(url)
            print(f'  judul : {t.js("document.title")}')
            print(f'  url   : {t.js("location.pathname")}')
            #  baca isi halaman penting
            ringkas = t.js(
                "(() => {const b=document.body.innerText||'';"
                "return b.replace(/\\s+/g,' ').slice(0,600);})()")
            print(f'  TEKS  : {ringkas}')
            t.potret(nama)
        finally:
            t.tutup()
    print('\nSELESAI')
