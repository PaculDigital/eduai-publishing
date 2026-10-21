"""Klien CDP lewat WebSocket MENTAH (tanpa pustaka `websocket`).

⚠️ TEMUAN 13Okt26: socket ke :9333 = CDP BROWSER-level ⇒ Page.* MENGGANTUNG.
   Cara benar: ambil `webSocketDebuggerUrl` dari /json/list (per-TAB).
"""
import base64
import json
import os
import socket
import struct
import urllib.request


class WS:
    def __init__(self, url, timeout=45):
        #  ws://host:port/path
        sisa = url.split('://', 1)[1]
        hostport, _, path = sisa.partition('/')
        host, _, port = hostport.partition(':')
        self.s = socket.create_connection((host, int(port or 80)),
                                          timeout=timeout)
        self.s.settimeout(timeout)
        kunci = base64.b64encode(os.urandom(16)).decode()
        req = (f'GET /{path} HTTP/1.1\r\nHost: {hostport}\r\n'
               'Upgrade: websocket\r\nConnection: Upgrade\r\n'
               f'Sec-WebSocket-Key: {kunci}\r\nSec-WebSocket-Version: 13\r\n'
               '\r\n')
        self.s.sendall(req.encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            buf += self.s.recv(4096)
        if b'101' not in buf.split(b'\r\n')[0]:
            raise RuntimeError('gagal upgrade: ' + buf[:120].decode('latin1'))
        self.i = 0
        self.buf = b''

    def _kirim(self, teks):
        data = teks.encode()
        n = len(data)
        head = b'\x81'
        if n < 126:
            head += struct.pack('!B', 0x80 | n)
        elif n < 65536:
            head += struct.pack('!BH', 0x80 | 126, n)
        else:
            head += struct.pack('!BQ', 0x80 | 127, n)
        mask = os.urandom(4)
        head += mask
        self.s.sendall(head + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _terima(self):
        while True:
            if len(self.buf) >= 2:
                b1, b2 = self.buf[0], self.buf[1]
                n = b2 & 0x7F
                off = 2
                if n == 126:
                    if len(self.buf) < 4:
                        pass
                    else:
                        n = struct.unpack('!H', self.buf[2:4])[0]
                        off = 4
                elif n == 127:
                    if len(self.buf) < 10:
                        pass
                    else:
                        n = struct.unpack('!Q', self.buf[2:10])[0]
                        off = 10
                if len(self.buf) >= off + n and not (n in (126, 127) and len(self.buf) < off):
                    payload = self.buf[off:off + n]
                    self.buf = self.buf[off + n:]
                    op = b1 & 0x0F
                    if op == 0x1:                       # teks
                        return payload.decode('utf-8', 'replace')
                    if op == 0x8:                       # close
                        raise RuntimeError('ws ditutup')
                    if op == 0x9:                       # ping → pong
                        self.s.sendall(b'\x8a\x80' + os.urandom(4))
                    continue
            potong = self.s.recv(1 << 20)
            if not potong:
                raise RuntimeError('ws kosong')
            self.buf += potong

    def cmd(self, metode, **par):
        self.i += 1
        self._kirim(json.dumps({'id': self.i, 'method': metode, 'params': par}))
        while True:
            d = json.loads(self._terima())
            if d.get('id') == self.i:
                if 'error' in d:
                    raise RuntimeError(str(d['error'])[:200])
                return d.get('result', {})


def tab_pertama(port=9333):
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list',
                                timeout=15) as f:
        tabs = json.load(f)
    for t in tabs:
        if t.get('type') == 'page':
            return t
    raise RuntimeError('tidak ada tab page')
