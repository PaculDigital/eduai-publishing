"""CARI NASKAH NYATA (05Okt26) — pakai Chrome CDP :9333 yang SUDAH hidup.
Tidak pakai browser-use (daemon-nya tak menemukan Chrome headless).

Tujuan: kumpulkan CALON naskah skripsi/tesis/disertasi full-text dari
Neliti / Garuda / repository kampus → untuk uji kedalaman peta halus.
"""
import json
import re
import socket
import struct
import sys
import time
import urllib.parse
import urllib.request

CDP = 'http://127.0.0.1:9333'
UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/151.0.0.0 Safari/537.36')


def baru(url: str) -> str:
    """Buka tab baru; kembalikan id tab."""
    u = f'{CDP}/json/new?{urllib.parse.quote(url, safe="")}'
    req = urllib.request.Request(u, method='PUT')
    return json.loads(urllib.request.urlopen(req, timeout=25).read())['id']


def tutup(tid: str) -> None:
    try:
        urllib.request.urlopen(f'{CDP}/json/close/{tid}', timeout=10).read()
    except Exception:                                          # noqa: BLE001
        pass


def html(url: str, tunggu: float = 4.0) -> str:
    """Buka tab, tunggu, ambil HTML setelah render."""
    tid = baru('about:blank')
    try:
        ws = None
        for t in json.loads(urllib.request.urlopen(f'{CDP}/json/list',
                                                   timeout=15).read()):
            if t['id'] == tid:
                ws = t['webSocketDebuggerUrl']
                break
        if not ws:
            return ''
        s = _ws(ws)
        s.kirim('Page.enable', {})
        s.kirim('Runtime.enable', {})
        s.kirim('Page.navigate', {'url': url})
        time.sleep(tunggu)
        r = s.kirim('Runtime.evaluate',
                    {'expression': 'document.documentElement.outerHTML',
                     'returnByValue': True})
        return (r.get('result', {}).get('result', {}) or {}).get('value') or ''
    finally:
        tutup(tid)


class _ws:
    """WebSocket CDP minimal (socket mentah) — pola _sketsa/potret_cdp.py."""

    def __init__(self, url: str) -> None:
        m = re.match(r'ws://([^:/]+):(\d+)(/.*)', url)
        host, port, jalur = m.group(1), int(m.group(2)), m.group(3)
        self.s = socket.create_connection((host, port), timeout=40)
        kunci = 'dGhlIHNhbXBsZSBub25jZQ=='
        self.s.sendall(
            f'GET {jalur} HTTP/1.1\r\nHost: {host}:{port}\r\n'
            f'Upgrade: websocket\r\nConnection: Upgrade\r\n'
            f'Sec-WebSocket-Key: {kunci}\r\nSec-WebSocket-Version: 13\r\n\r\n'
            .encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            buf += self.s.recv(4096)
        self.buf = buf.split(b'\r\n\r\n', 1)[1]
        self.n = 0

    def _kirim_bingkai(self, data: bytes) -> None:
        p = bytearray([0x81])
        L = len(data)
        if L < 126:
            p.append(0x80 | L)
        elif L < (1 << 16):
            p.append(0x80 | 126)
            p += struct.pack('>H', L)
        else:
            p.append(0x80 | 127)
            p += struct.pack('>Q', L)
        mask = b'\x01\x02\x03\x04'
        p += mask
        p += bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        self.s.sendall(bytes(p))

    def _baca_bingkai(self) -> bytes:
        def _baca(n: int) -> bytes:
            d = b''
            while len(d) < n:
                c = self.s.recv(n - len(d))
                if not c:
                    raise ConnectionError('tutup')
                d += c
            return d
        h = self.buf[:2] if len(self.buf) >= 2 else _baca(2)
        self.buf = self.buf[2:] if len(self.buf) >= 2 else b''
        L = h[1] & 0x7F
        if L == 126:
            L = struct.unpack('>H', _baca(2))[0]
        elif L == 127:
            L = struct.unpack('>Q', _baca(8))[0]
        return _baca(L)

    def kirim(self, metode: str, params: dict) -> dict:
        self.n += 1
        self._kirim_bingkai(json.dumps({'id': self.n, 'method': metode,
                                        'params': params}).encode())
        for _ in range(40):
            try:
                pesan = json.loads(self._baca_bingkai())
            except Exception:                                  # noqa: BLE001
                return {}
            if pesan.get('id') == self.n:
                return pesan.get('result', {})
        return {}


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else \
        'https://www.neliti.com/id/search?q=skripsi'
    print('URL:', target)
    h = html(target)
    print('panjang HTML:', len(h))
    # cari tautan PDF / detail
    tautan = sorted(set(re.findall(
        r'href="(https?://[^"]+\.pdf[^"]*)"', h, re.I)))
    print('PDF langsung:', len(tautan))
    for t in tautan[:15]:
        print('  PDF:', t[:150])
    det = sorted(set(re.findall(
        r'href="(https?://(?:www\.)?(?:neliti|garuda|repository|etd)[^"]*)"',
        h, re.I)))
    print('halaman detail:', len(det))
    for t in det[:15]:
        print('  DET:', t[:150])
    with open('/tmp/cari_naskah.html', 'w') as f:
        f.write(h)


if __name__ == '__main__':
    main()
