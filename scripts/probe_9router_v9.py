#!/usr/bin/env python3
"""PROBE v9 — bedah respons MENTAH (max_tokens 2000) baris per baris."""
import json
import re
import urllib.request

teks = open('/opt/data/config.yaml').read()
m = re.search(r'api_key:\s*([^\s]+)\s*\n\s*base_url:\s*(http://172\.17\.0\.1:20128/v1)',
              teks)
KEY, BASE = m.group(1).strip('\'"'), m.group(2)
HDR = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}

PESAN = ('Perbaiki kalimat tesis berikut sesuai PUEBI. '
         'Balas HANYA kalimat hasil, tanpa penjelasan:\n\n'
         'Berdasarkan hasil penelitian yang telah dilaksanakan diatas, '
         'maka dapat ditarik kesimpulan bahwa data yang penulis kumpulkan '
         'adalah tidak signifikan secara statistic.')

body = json.dumps({'model': 'inferhub/ag/claude-sonnet-4-6',
                   'messages': [{'role': 'user', 'content': PESAN}],
                   'max_tokens': 2000}).encode()
req = urllib.request.Request(BASE + '/chat/completions', data=body,
                             headers=HDR, method='POST')
with urllib.request.urlopen(req, timeout=240) as r:
    raw = r.read().decode()

print('Content-Type :', r.headers.get('Content-Type'))
print('TOTAL CHARS  :', len(raw))
print('JUMLAH BARIS :', len(raw.splitlines()))
print()
for i, baris in enumerate(raw.splitlines()):
    b = baris.strip()
    if not b:
        print(f'[{i}] (kosong)')
        continue
    print(f'[{i}] len={len(b)} awal={b[:100]!r}')
    if i > 25:
        print('... (dipotong, total', len(raw.splitlines()), 'baris)')
        break
