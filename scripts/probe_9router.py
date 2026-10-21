#!/usr/bin/env python3
"""PROBE 9router — cek kesehatan untuk benchmark AI-doc (TANPA menampilkan key).

Output hanya: status, jumlah model, daftar model, waktu respons.
"""
import json
import time
import urllib.request

BASE = 'http://172.17.0.1:20128/v1'

# ambil key dari auth.json (tidak di-print)
_au = json.load(open('/opt/data/auth.json'))
KEY = None
for pool, items in _au.get('credential_pool', {}).items():
    for it in items:
        if '20128' in (it.get('base_url') or ''):
            KEY = it.get('api_key') or it.get('key')
            break
if not KEY:
    # fallback: hermes config
    import os
    KEY = os.environ.get('9ROUTER_KEY', '')
    print('PERINGATAN: key tidak ditemukan di auth.json, cek env')

HDR = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}


def get(path):
    t0 = time.time()
    req = urllib.request.Request(BASE + path, headers=HDR)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
        return r.status, data, round(time.time() - t0, 2)


print('── /models ──')
try:
    st, data, dt = get('/models')
    model = [m.get('id') for m in data.get('data', [])]
    print('status     :', st)
    print('jumlah    :', len(model))
    print('contoh    :', model[:15])
    print('waktu     :', dt, 'detik')
except Exception as e:
    print('GAGAL:', type(e).__name__, str(e)[:200])

print()
print('── chat test kecil ──')
try:
    t0 = time.time()
    body = json.dumps({
        'model': model[0] if 'model' in dir() and model else 'gpt-4o-mini',
        'messages': [{'role': 'user', 'content': 'Balas hanya: OK'}],
        'max_tokens': 8,
    }).encode()
    req = urllib.request.Request(BASE + '/chat/completions', data=body, headers=HDR,
                                 method='POST')
    with urllib.request.urlopen(req, timeout=60) as r:
        hasil = json.loads(r.read().decode())
        print('status     :', r.status)
        print('jawaban   :', hasil['choices'][0]['message']['content'][:100])
        print('model     :', hasil.get('model'))
        print('latensi   :', round(time.time() - t0, 2), 'detik')
except Exception as e:
    print('GAGAL:', type(e).__name__, str(e)[:300])
