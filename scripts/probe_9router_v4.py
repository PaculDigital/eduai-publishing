#!/usr/bin/env python3
"""PROBE 9router v4 — lihat isi MENTAH respons chat (bukan json.loads)."""
import json
import re
import time
import urllib.request

teks = open('/opt/data/config.yaml').read()
m = re.search(r'api_key:\s*([^\s]+)\s*\n\s*base_url:\s*(http://172\.17\.0\.1:20128/v1)',
              teks)
KEY, BASE = m.group(1).strip('\'"'), m.group(2)
HDR = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}

t0 = time.time()
body = json.dumps({'model': '9router',
                   'messages': [{'role': 'user', 'content': 'Balas hanya: OK'}],
                   'max_tokens': 8}).encode()
req = urllib.request.Request(BASE + '/chat/completions', data=body,
                             headers=HDR, method='POST')
with urllib.request.urlopen(req, timeout=120) as r:
    raw = r.read().decode()
    print('status :', r.status)
    print('tipe   :', r.headers.get('Content-Type'))
    print('panjang:', len(raw))
    print('isi    :', raw[:600])
    print('t      :', round(time.time() - t0, 2), 's')

    # coba parse SSE kalau bentuknya stream
    if 'text/event-stream' in (r.headers.get('Content-Type') or '') or raw.startswith('data:'):
        for baris in raw.splitlines():
            if baris.startswith('data:') and '[DONE]' not in baris:
                try:
                    d = json.loads(baris[5:])
                    c = d.get('choices', [{}])[0]
                    delta = c.get('delta', {}).get('content') or c.get('message', {}).get('content')
                    if delta:
                        print('jawab  :', delta[:80])
                        break
                except Exception:
                    pass
