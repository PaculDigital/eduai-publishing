#!/usr/bin/env python3
"""POTRET DUA DASHBOARD: MAHASISWA ↔ PEMBIMBING (standar 25Sep26).

Menjawab pertanyaan Bos: apakah dashboard mahasiswa & pembimbing SINKRON,
dan apakah catatan pembimbing TERLIHAT JELAS oleh mahasiswa?

ALAT RESMI: _sketsa/potret_cdp.py (socket mentah, CDP :9333) — JANGAN ganti.
PROFIL: pakai profil yang disiapkan scripts/rawat_potret.sh --mulai.

DATA UJI (dari DB produksi):
  mahasiswa  : user 3 (Wulan)
  berkas     : file 9 — TESIS_LENGKAP_Goras.docx
  pembimbingan: 84 — "Uji Sorotan 3.1" (punya catatan pembimbing id 106)
  catatan    : id 106 — 'Catatan uji sorotan A' di BAB I — PENDAHULUAN

JALAN DI HOST (Chrome di host, :9333).
"""
import os
import subprocess
import sys

BASE = 'https://eduai.bikinaja.id'
KELUAR = '/opt/data/services/eduai-publishing/_sketsa/bukti_sinkron'
os.makedirs(KELUAR, exist_ok=True)

#  ── ambil token uji dari container ──────────────────────────────────────
def token_untuk(user_id: int) -> str:
    r = subprocess.run(
        ['docker', 'exec', 'eduai-app', 'python3', '-c',
         f'from app.auth import buat_token; print(buat_token({user_id}))'],
        capture_output=True, text=True, timeout=60)
    return r.stdout.strip()


TOKEN_MHS = token_untuk(3)
print(f'token mahasiswa (user 3): {len(TOKEN_MHS)} karakter')

#  ── daftar halaman yang dipotret ────────────────────────────────────────
HALAMAN = [
    #  (nama berkas, url, lebar, tinggi, keterangan)
    ('mhs-01-beranda.png',   f'{BASE}/',                 1500, 1000,
     'Beranda mahasiswa — daftar naskah'),
    ('mhs-02-naskah.png',    f'{BASE}/naskah',           1500, 1100,
     'Halaman Naskah mahasiswa — daftar berkas'),
    ('mhs-03-editor.png',    f'{BASE}/edit/9',           1500, 1200,
     'Editor naskah mahasiswa — apakah catatan terlihat'),
    ('mhs-04-bagikan.png',   f'{BASE}/bagikan/9',        1500, 1200,
     'Bagikan ke pembimbing'),
]

#  ── set cookie login lewat CDP, lalu potret ─────────────────────────────
SCRIPT_POTRET = '/opt/data/services/eduai-publishing/_sketsa/potret_cdp.py'


def potret_dengan_login(nama, url, lebar, tinggi, ket):
    """Potret dengan cookie login disuntik lewat CDP."""
    import json as _json
    import socket as _socket
    import base64
    import urllib.request

    CDP = 'http://127.0.0.1:9333'
    #  tab baru
    req = urllib.request.Request(f'{CDP}/json/new?about:blank', method='PUT')
    try:
        tab = _json.loads(urllib.request.urlopen(req, timeout=15).read())
    except Exception:                                                     # noqa: BLE001
        tab = _json.loads(urllib.request.urlopen(
            f'{CDP}/json/new?about:blank', timeout=15).read())
    tid = tab['id']
    ws = tab['webSocketDebuggerUrl']
    #  ws://127.0.0.1:9333/devtools/page/XXX
    sisa = ws.split('://', 1)[1]
    hostport, path = sisa.split('/', 1)

    s = _socket.create_connection(
        (hostport.split(':')[0], int(hostport.split(':')[1])), timeout=30)
    kunci = base64.b64encode(os.urandom(16)).decode()
    s.sendall((
        f'GET /{path} HTTP/1.1\r\nHost: {hostport}\r\n'
        'Upgrade: websocket\r\nConnection: Upgrade\r\n'
        f'Sec-WebSocket-Key: {kunci}\r\nSec-WebSocket-Version: 13\r\n'
        'Origin: http://127.0.0.1:9333\r\n\r\n').encode())
    buf = b''
    while b'\r\n\r\n' not in buf:
        buf += s.recv(4096)

    _id = [0]

    def kirim(metode, params=None):
        _id[0] += 1
        pesan = _json.dumps({'id': _id[0], 'method': metode,
                             'params': params or {}})
        data = pesan.encode()
        mask = os.urandom(4)
        topeng = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        if len(data) < 126:
            hdr = bytes([0x81, 0x80 | len(data)])
        else:
            hdr = bytes([0x81, 0x80 | 126]) + len(data).to_bytes(2, 'big')
        s.sendall(hdr + mask + topeng)
        return _id[0]

    def terima():
        h = s.recv(2)
        if not h:
            return None
        n = h[1] & 0x7F
        if n == 126:
            n = int.from_bytes(s.recv(2), 'big')
        elif n == 127:
            n = int.from_bytes(s.recv(8), 'big')
        data = b''
        while len(data) < n:
            data += s.recv(n - len(data))
        return _json.loads(data)

    def cmd(metode, params=None, tunggu_id=None):
        kirim(metode, params)
        while True:
            m = terima()
            if m is None:
                return None
            if m.get('id') == tunggu_id or 'id' in m:
                return m

    #  set cookie login
    cid = kirim('Network.setCookie', {
        'name': 'eduai_session', 'value': TOKEN_MHS,
        'domain': 'eduai.bikinaja.id', 'path': '/',
        'secure': True, 'httpOnly': True,
    })
    cmd('Network.setCookie', {
        'name': 'eduai_session', 'value': TOKEN_MHS,
        'domain': 'eduai.bikinaja.id', 'path': '/', 'secure': True,
    })
    #  buka URL
    kirim('Page.enable')
    kirim('Page.navigate', {'url': url})
    import time
    time.sleep(8)
    kirim('Emulation.setDeviceMetricsOverride', {
        'width': lebar, 'height': tinggi, 'deviceScaleFactor': 1,
        'mobile': False})
    time.sleep(2)
    pid = kirim('Page.captureScreenshot', {'format': 'png'})
    hasil = None
    for _ in range(60):
        m = terima()
        if m is None:
            break
        if m.get('id') == pid:
            hasil = m
            break
    s.close()
    urllib.request.urlopen(f'{CDP}/json/close/{tid}', timeout=10).read()

    if hasil and hasil.get('result', {}).get('data'):
        jalur = os.path.join(KELUAR, nama)
        with open(jalur, 'wb') as f:
            f.write(base64.b64decode(hasil['result']['data']))
        ukuran = os.path.getsize(jalur)
        tanda = '✅' if ukuran > 10000 else '⚠️'
        print(f'  {tanda} {nama} — {ukuran} byte · {ket}')
        return jalur
    print(f'  ❌ {nama} — gagal')
    return None


if __name__ == '__main__':
    print('═' * 74)
    print('  POTRET DUA DASHBOARD — STANDAR 25Sep26')
    print('═' * 74)
    print()
    print(f'KELUAR: {KELUAR}')
    print()
    for nama, url, lebar, tinggi, ket in HALAMAN:
        potret_dengan_login(nama, url, lebar, tinggi, ket)
    print()
    print('SELESAI')
