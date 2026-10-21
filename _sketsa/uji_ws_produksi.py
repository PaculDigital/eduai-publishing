"""Uji WS /oo/aset lewat domain produksi (Cloudflare) — apakah tersambung?

Akar dugaan: onDocumentReady TIDAK PERNAH datang -> loading nyangkut.
Event itu lewat socket.io (WebSocket). Kalau WS gagal lewat CF, editor
tidak pernah "siap".
"""
import base64
import os
import socket
import ssl
import struct


def coba_ws(host, path, pakai_ssl=True, timeout=20):
    """Coba handshake WebSocket; balik status baris pertama."""
    try:
        raw = socket.create_connection((host, 443 if pakai_ssl else 80),
                                       timeout=timeout)
        if pakai_ssl:
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(raw, server_hostname=host)
        else:
            s = raw
        k = base64.b64encode(os.urandom(16)).decode()
        s.sendall((
            'GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\n'
            'Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n'
            'Sec-WebSocket-Version: 13\r\nOrigin: https://%s\r\n\r\n'
            % (path, host, k, host)).encode())
        s.settimeout(timeout)
        b = s.recv(400)
        s.close()
        return b.split(b'\r\n')[0].decode(errors='replace'), b.decode(
            errors='replace')[:200]
    except Exception as e:
        return 'GALAT: ' + str(e)[:90], ''


UJI = [
    ('/oo/aset/socket.io/?EIO=4&transport=websocket', True),
    ('/oo/aset/9.4.0-884b8d735f24a691228ffc46e8d0719b/doc/x/c/?EIO=4&transport=websocket', True),
]
for p, ssl_on in UJI:
    baris, isi = coba_ws('eduai.bikinaja.id', p, ssl_on)
    print('%-74s' % p[:74])
    print('   → %s' % baris)
    if '101' in baris:
        print('   ✅ WS TERSAMBUNG')
    elif 'HTTP/1.1 4' in baris or 'HTTP/1.1 5' in baris:
        print('   ❌ DITOLAK —', isi.split('\r\n\r\n')[-1][:80])
    print()
