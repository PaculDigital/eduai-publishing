#!/usr/bin/env python3
"""POTRET EDITOR ONLYOFFICE HIDUP — lihat menu kolaborasi & fitur yang ada.

Standar 25Sep26: potret_cdp.py (socket mentah · CDP :9333).
Tujuan: jawab pertanyaan Bos —
   · menu kolaborasi apa saja yang MUNCUL di editor kita?
   · apakah ada fitur AI bawaan OO?
   · bagaimana bentuk komentar & track changes?
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
KELUAR = ('/opt/data/services/eduai-publishing/_sketsa/bukti_oo_menu')
os.makedirs(KELUAR, exist_ok=True)


def tok():
    r = subprocess.run(
        ['docker', 'exec', 'eduai-app', 'python3', '-c',
         'from app.auth import buat_token; print(buat_token(3))'],
        capture_output=True, text=True, timeout=60)
    return r.stdout.strip().splitlines()[-1]


class T:
    def __init__(s, lb=1600, tg=1000):
        req = urllib.request.Request(f'{CDP}/json/new?about:blank',
                                     method='PUT')
        try:
            t = json.loads(urllib.request.urlopen(req, timeout=15).read())
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
        s.lb, s.tg = lb, tg

    def kr(s, m, p):
        s.i += 1
        d = json.dumps({'id': s.i, 'method': m, 'params': p or {}}).encode()
        mk = os.urandom(4)
        tp = bytes(x ^ mk[j % 4] for j, x in enumerate(d))
        h = (bytes([0x81, 0x80 | len(d)]) if len(d) < 126
             else bytes([0x81, 0x80 | len(d)]) if len(d) < 126
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
        for _ in range(600):
            r = s.tr()
            if r is None:
                return None
            if r.get('id') == pid:
                return r
        return None

    def js(s, e, frame=None):
        p = {'expression': e, 'returnByValue': True, 'awaitPromise': True}
        if frame:
            p['contextId'] = frame
        r = s.cmd('Runtime.evaluate', p)
        try:
            return r['result']['result'].get('value')
        except Exception:                                                 # noqa: BLE001
            return None

    def potret(s, n):
        r = s.cmd('Page.captureScreenshot', {'format': 'png'})
        if not (r and r.get('result', {}).get('data')):
            print(f'  ❌ {n}')
            return None
        j = os.path.join(KELUAR, n)
        open(j, 'wb').write(base64.b64decode(r['result']['data']))
        print(f'  ✅ {n} — {os.path.getsize(j)} byte')
        return j

    def tutup(s):
        try:
            s.s.close()
        except Exception:                                                 # noqa: BLE001
            pass
        try:
            urllib.request.urlopen(f'{CDP}/json/close/{s.tid}',
                                   timeout=10).read()
        except Exception:                                                 # noqa: BLE001
            pass


TK = tok()
print(f'token: {TK[:16]}…')
t = T()
t.cmd('Network.setCookie', {'name': 'eduai_session', 'value': TK,
                            'domain': 'eduai.bikinaja.id', 'path': '/',
                            'secure': True})
t.cmd('Page.enable')
print()
print('══ BUKA EDITOR OO (dokumen 9) ══')
t.cmd('Page.navigate', {'url': f'{BASE}/edit/9'})
print('  menunggu OO memuat (55 dtk)…')
time.sleep(55)

print()
print('  judul halaman:', t.js('document.title'))
print('  iframe:', t.js("document.querySelector('iframe')?document.querySelector"
                     "('iframe').src.slice(0,70):'TIDAK ADA'"))
t.potret('oo-01-editor.png')

#  daftar target (frame OO terpisah)
print()
print('══ TARGET/FRAME di browser ══')
r = subprocess.run(['curl', '-s', '-m', '10', f'{CDP}/json/list'],
                   capture_output=True, text=True, timeout=30)
try:
    for x in json.loads(r.stdout):
        u = (x.get('url') or '')[:90]
        print(f"  • {x.get('type')} | {u}")
except Exception as e:                                                    # noqa: BLE001
    print('  gagal baca:', e)

print()
print('══ MENU DI HALAMAN (teks yang tampak) ══')
tx = t.js("(()=>{const b=document.body.innerText||'';"
          "return b.replace(/\\s+/g,' ').slice(0,900)})()")
print(' ', tx)
print()
print('══ TOMBOL DI TOOLBAR (judul/title) ══')
tbl = t.js("(()=>{const a=[...document.querySelectorAll('button,[class*=btn],"
           "[class*=toolbar] *')].map(e=>(e.getAttribute('title')||"
           "e.getAttribute('aria-label')||'').trim()).filter(x=>x.length>2);"
           "return [...new Set(a)].slice(0,40).join(' | ')})()")
print(' ', tbl if tbl else '(tidak terbaca dari frame utama — OO di iframe)')

t.tutup()
print()
print('SELESAI')
