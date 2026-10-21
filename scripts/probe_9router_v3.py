#!/usr/bin/env python3
"""PROBE 9router v3 — parse config.yaml TANPA pyyaml (manual), key tidak di-print."""
import json
import re
import time
import urllib.request

teks = open('/opt/data/config.yaml').read()
# blok: custom: ... api_key: xxx ... base_url: ...20128...
m = re.search(r'api_key:\s*([^\s]+)\s*\n\s*base_url:\s*(http://172\.17\.0\.1:20128/v1)',
              teks)
if not m:
    raise SystemExit('key 9router tidak ketemu di config.yaml')
KEY, BASE = m.group(1).strip('\'"'), m.group(2)
HDR = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}

# 1. daftar model
t0 = time.time()
req = urllib.request.Request(BASE + '/models', headers=HDR)
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.loads(r.read().decode())
model = [m.get('id') for m in data.get('data', [])]
print('models   : status', r.status, '| jumlah', len(model), '| t', round(time.time() - t0, 2), 's')
print('daftar   :', model[:20])

# 2. chat mini — bukti model jalan
t0 = time.time()
body = json.dumps({'model': model[0] if model else '9router',
                   'messages': [{'role': 'user', 'content': 'Balas hanya: OK'}],
                   'max_tokens': 8}).encode()
req = urllib.request.Request(BASE + '/chat/completions', data=body,
                             headers=HDR, method='POST')
with urllib.request.urlopen(req, timeout=120) as r:
    hasil = json.loads(r.read().decode())
print('chat     : status', r.status, '| jawab:',
      hasil['choices'][0]['message']['content'][:60].strip(),
      '| model:', hasil.get('model'), '| t', round(time.time() - t0, 2), 's')
