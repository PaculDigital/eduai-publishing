"""UJI BACA: apakah WebSocket /oo/aset tersambung lewat domain produksi?

Bandingkan TANPA cookie vs DENGAN cookie sesi sah. Ini uji BACA saja
(handshake, tidak mengubah data apa pun) — untuk memastikan akarnya:
kalau tanpa-cookie 403 tapi dengan-cookie 101, berarti WS SEHAT dan
masalahnya di tempat lain. Kalau dua-duanya 403, WS diputus di depan.
"""
import base64
import os
import socket
import ssl
import subprocess

DOMAIN = 'eduai.bikinaja.id'
USER = 3

tok = subprocess.run(
    ['docker', 'exec', '-i', '-w', '/app', 'eduai-app', 'python3', '-'],
    input=("import sys;sys.path.insert(0,'/app')\n"
           "from app.auth import buat_token\n"
           "print(buat_token(%d))" % USER).encode(),
    capture_output=True).stdout.decode().strip()
print('token user %d diperoleh: %s...' % (USER, tok[:20]))


def coba(path, cookie=None, timeout=25):
    try:
        raw = socket.create_connection((DOMAIN, 443), timeout=timeout)
        s = ssl.create_default_context().wrap_socket(raw, server_hostname=DOMAIN)
        k = base64.b64encode(os.urandom(16)).decode()
        hdr = ('GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\n'
               'Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n'
               'Sec-WebSocket-Version: 13\r\nOrigin: https://%s\r\n'
               % (path, DOMAIN, k, DOMAIN))
        if cookie:
            hdr += 'Cookie: eduai_session=%s\r\n' % cookie
        s.sendall((hdr + '\r\n').encode())
        s.settimeout(timeout)
        b = s.recv(400)
        s.close()
        baris = b.split(b'\r\n')[0].decode(errors='replace')
        sisa = b.decode(errors='replace')
        return baris, sisa
    except Exception as e:
        return 'GALAT: ' + str(e)[:100], ''


H = '884b8d735f24a691228ffc46e8d0719b'
PATH = '/oo/aset/9.4.0-%s/doc/x/c/?EIO=4&transport=websocket' % H

for judul, ck in [('TANPA cookie', None), ('DENGAN cookie sesi', tok)]:
    baris, sisa = coba(PATH, ck)
    print()
    print('%-20s → %s' % (judul, baris))
    if ' 101' in baris:
        print('   ✅ WS TERSAMBUNG (Cloudflare & app meneruskan WebSocket)')
    elif ' 403' in baris:
        print('   ❌ 403 — ditolak')
    elif ' 303' in baris:
        print('   ⚠️ 303 — diminta login (cookie tidak diterima)')
    # tampilkan baris server
    for ln in sisa.split('\r\n'):
        if ln.lower().startswith('server:'):
            print('   server:', ln.split(':', 1)[1].strip())
