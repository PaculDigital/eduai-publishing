#!/usr/bin/env python3
"""Baca isi halaman Chrome lewat CDP (websocket) — alat potret/baca DOM.

Cara pakai:
    uv run --with websocket-client baca_cdp.py <tab_id> innerText
    uv run --with websocket-client baca_cdp.py <tab_id> title
"""
import json
import sys
import time
import urllib.request

import websocket   # websocket-client

CDP = 'http://127.0.0.1:9333'


def tab_ws(tab_id):
    for x in json.loads(urllib.request.urlopen(CDP + '/json/list', timeout=15).read()):
        if x.get('id') == tab_id:
            return x.get('webSocketDebuggerUrl')
    return None


def main():
    tab = sys.argv[1]
    aksi = sys.argv[2] if len(sys.argv) > 2 else 'innerText'
    ws = websocket.create_connection(tab_ws(tab), timeout=25,
                                     suppress_origin=True)
    if aksi == 'title':
        expr = 'document.title'
    elif aksi == 'links':
        expr = ("JSON.stringify([...document.querySelectorAll('a[href]')]"
                ".map(a=>a.href+' || '+a.innerText.trim()).slice(0,80))")
    elif aksi == 'raw':
        expr = sys.argv[3]
    else:
        expr = 'document.body.innerText'
    ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate',
                        'params': {'expression': expr, 'returnByValue': True}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get('id') == 1:
            r = msg.get('result', {}).get('result', {})
            print(r.get('value') or r)
            break
    ws.close()


if __name__ == '__main__':
    main()
