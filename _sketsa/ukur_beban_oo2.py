#!/usr/bin/env python3
"""UKUR BEBAN OO: 1 sesi vs 2 sesi (dokumen SAMA) — angka nyata.

Jalankan sesudah _sketsa/ukur_beban_oo.sh (yang membuka sesi ke-1).
Skrip ini membuka sesi ke-2 (mode view, seperti pembimbing) pada
dokumen yang sama, lalu melaporkan RAM oo-converter tiap tahap.
"""
import base64
import json
import os
import socket
import subprocess
import time
import urllib.request

CDP = 'http://127.0.0.1:9333'
BASE = 'https://eduai.bikinaja.id'


def ram_oo():
    r = subprocess.run(['docker', 'stats', 'oo-converter', '--no-stream',
                        '--format', '{{.MemUsage}}'],
                       capture_output=True, text=True, timeout=60)
    return r.stdout.strip().split('/')[0].strip()


def ram_server():
    r = subprocess.run(['free', '-m'], capture_output=True, text=True, timeout=30)
    for ln in r.stdout.splitlines():
        if ln.startswith('Mem:'):
            p = ln.split()
            return f'{p[2]} MB terpakai dari {p[1]} MB'
    return '?'


def token_uji():
    r = subprocess.run(
        ['docker', 'exec', 'eduai-app', 'python3', '-c',
         'from app.auth import buat_token; print(buat_token(3))'],
        capture_output=True, text=True, timeout=60)
    return r.stdout.strip().splitlines()[-1]


class Tab:
    def __init__(s):
        r = urllib.request.Request(f'{CDP}/json/new?about:blank', method='PUT')
        try:
            t = json.loads(urllib.request.urlopen(r, timeout=15).read())
        except Exception:                                                 # noqa: BLE001
            t = json.loads(urllib.request.urlopen(
                f'{CDP}/json/new?about:blank', timeout=15).read())
        s.tid = t['id']
        hp, path = t['webSocketDebuggerUrl'].split('://', 1)[1].split('/', 1)
        s.s = socket.create_connection(
            (hp.split(':')[0], int(hp.split(':')[1])), timeout=120)
        k = base64.b64encode(os.urandom(16)).decode()
        s.s.sendall((
            f'GET /{path} HTTP/1.1\r\nHost: {hp}\r\nUpgrade: websocket\r\n'
            f'Connection: Upgrade\r\nSec-WebSocket-Key: {k}\r\n'
            'Sec-WebSocket-Version: 13\r\n\r\n').encode())
        b = b''
        while b'\r\n\r\n' not in b:
            b += s.s.recv(4096)
        s.i = 0

    def kr(s, m, p):
        s.i += 1
        d = json.dumps({'id': s.i, 'method': m, 'params': p or {}}).encode()
        mk = os.urandom(4)
        tp = bytes(x ^ mk[j % 4] for j, x in enumerate(d))
        h = (bytes([0x81, 0x80 | len(d)]) if len(d) < 126
             else bytes([0x81, 0x80 | 126]) + len(d).to_bytes(2, 'big'))
        s.s.sendall(h + mk + tp)
        return s.i

    def tr(s):
        h = s.s.recv(2)
        if not h:
            return None
        n = h[1] & 0x7F
        if n == 126:
            n = int.from_bytes(s.s.recv(2), 'big')
        elif n == 127:
            n = int.from_bytes(s.s.recv(8), 'big')
        d = b''
        while len(d) < n:
            d += s.s.recv(n - len(d))
        return json.loads(d)

    def cmd(s, m, p=None):
        pid = s.kr(m, p)
        for _ in range(500):
            r = s.tr()
            if r is None:
                return None
            if r.get('id') == pid:
                return r
        return None

    def js(s, e):
        r = s.cmd('Runtime.evaluate', {'expression': e, 'returnByValue': True})
        try:
            return r['result']['result'].get('value')
        except Exception:                                                 # noqa: BLE001
            return None


TOK = token_uji()
print(f'token uji: {TOK[:18]}…')
print()
print('══ TAHAP 1: RAM sebelum sesi ke-2 ══')
print(f'   oo-converter : {ram_oo()}')
print(f'   server       : {ram_server()}')

print()
print('══ TAHAP 2: BUKA SESI KE-2 (pembimbing — /tinjau, DIBIARKAN di halaman) ══')
t = Tab()
t.cmd('Network.setCookie', {'name': 'eduai_session', 'value': TOK,
                            'domain': 'eduai.bikinaja.id', 'path': '/',
                            'secure': True})
t.cmd('Page.enable')
#  Tanpa token mentah, halaman /edit/9 saja (sesi OO KEDUA dokumen yang sama)
t.cmd('Page.navigate', {'url': f'{BASE}/edit/9'})
print('   menunggu OO memuat (60 dtk)…')
time.sleep(60)
r = t.js("document.querySelector('iframe')?document.querySelector('iframe')"
         ".src.slice(0,70):'TIDAK ADA IFRAME'")
print(f'   iframe ke-2  : {r}')
print(f'   oo-converter : {ram_oo()}')
print(f'   server       : {ram_server()}')

print()
print('══ TAHAP 3: stabil (tunggu 15 dtk) ══')
time.sleep(15)
print(f'   oo-converter : {ram_oo()}')
print(f'   server       : {ram_server()}')
print()
print(f'tab ke-2 id = {t.tid}  (DIBIARKAN terbuka untuk ukur beban puncak)')
open('/tmp/oo_tab_2.txt', 'w').write(t.tid)
