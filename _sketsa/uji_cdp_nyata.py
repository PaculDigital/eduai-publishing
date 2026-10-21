"""UJI CDP NYATA — bikin tab, buka halaman, potret. 11Okt26.
Bukan cuma cek port: harus benar-benar menghasilkan PNG.
"""
import base64
import json
import urllib.request

CDP = 'http://127.0.0.1:9333'
OUT = '/opt/data/services/eduai-publishing/_sketsa/uji-cdp-hasil.png'


def cdp_http(path, metode='GET'):
    req = urllib.request.Request(CDP + path, method=metode)
    with urllib.request.urlopen(req, timeout=15) as r:
        isi = r.read().decode().strip()
    if not isi:
        return {}
    try:
        return json.loads(isi)
    except json.JSONDecodeError:
        return {'_mentah': isi[:120]}


def ws_kirim(ws_url, pesan_list):
    """Kirim daftar perintah CDP lewat WebSocket, balas list hasil."""
    import socket
    import struct
    from urllib.parse import urlparse

    u = urlparse(ws_url)
    s = socket.create_connection((u.hostname, u.port), timeout=20)
    key = base64.b64encode(b'wulan-uji-cdp-11okt26').decode()
    s.sendall((
        'GET %s HTTP/1.1\r\nHost: %s:%s\r\nUpgrade: websocket\r\n'
        'Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n'
        'Sec-WebSocket-Version: 13\r\n\r\n'
        % (u.path, u.hostname, u.port, key)).encode())

    # baca handshake sampai \r\n\r\n
    buf = b''
    while b'\r\n\r\n' not in buf:
        buf += s.recv(4096)

    def bingkai(payload):
        data = payload.encode()
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
        mask = b'\x11\x22\x33\x44'
        head += mask
        return bytes(head) + bytes(b ^ mask[i % 4] for i, b in enumerate(data))

    def baca():
        h = s.recv(2)
        if len(h) < 2:
            return None
        panjang = h[1] & 0x7F
        if panjang == 126:
            panjang = struct.unpack('>H', s.recv(2))[0]
        elif panjang == 127:
            panjang = struct.unpack('>Q', s.recv(8))[0]
        data = b''
        while len(data) < panjang:
            potong = s.recv(panjang - len(data))
            if not potong:
                break
            data += potong
        return data.decode('utf-8', 'replace')

    hasil = []
    for p in pesan_list:
        s.sendall(bingkai(json.dumps(p)))
        # tunggu balasan dengan id yang cocok (buang event tanpa id)
        for _ in range(40):
            teks = baca()
            if teks is None:
                break
            try:
                j = json.loads(teks)
            except Exception:
                continue
            if 'id' in j and j['id'] == p['id']:
                hasil.append(j)
                break
    s.close()
    return hasil


# 1. buat tab baru
tab = cdp_http('/json/new?about:blank', 'PUT')
print('TAB BARU:', tab.get('id', '?'), '| ws:', bool(tab.get('webSocketDebuggerUrl')))
ws = tab['webSocketDebuggerUrl']

# 2. navigasi + ukur + potret
perintah = [
    {'id': 1, 'method': 'Page.enable'},
    {'id': 2, 'method': 'Emulation.setDeviceMetricsOverride',
     'params': {'width': 900, 'height': 700, 'deviceScaleFactor': 1, 'mobile': False}},
    {'id': 3, 'method': 'Runtime.evaluate',
     'params': {'expression': (
         "document.body.innerHTML='<div style=\"font:16px sans-serif;padding:30px\">"
         "<h1 style=\"color:#c53030\">CDP HIDUP</h1>"
         "<p>Chrome 146 · potret dari WebSocket CDP</p></div>'; "
         "document.title='UJI-CDP'; 'isi-ok'"), 'returnByValue': True}},
    {'id': 4, 'method': 'Runtime.evaluate',
     'params': {'expression': 'document.body.innerText', 'returnByValue': True}},
    {'id': 5, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}},
]

keluar = ws_kirim(ws, perintah)
by_id = {k['id']: k for k in keluar}

teks = by_id.get(4, {}).get('result', {}).get('result', {}).get('value', '')
print('TEKS HALAMAN:', repr(teks[:60]))

png = by_id.get(5, {}).get('result', {}).get('data', '')
if png:
    with open(OUT, 'wb') as f:
        f.write(base64.b64decode(png))
    import os
    print('PNG:', OUT, os.path.getsize(OUT), 'byte')
else:
    print('PNG: GAGAL')

# 3. bersihkan tab
cdp_http('/json/close/' + tab['id'])
print('TAB DITUTUP')

lulus = ('CDP HIDUP' in teks) and bool(png)
print()
print('HASIL UJI CDP:', 'LULUS' if lulus else 'GAGAL')
raise SystemExit(0 if lulus else 1)
