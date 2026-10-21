#!/usr/bin/env python3
"""PROBE v6 — lihat isi MENTAH respons inferhub (model tercepat)."""
import json
import re
import urllib.request

teks = open('/opt/data/config.yaml').read()
m = re.search(r'api_key:\s*([^\s]+)\s*\n\s*base_url:\s*(http://172\.17\.0\.1:20128/v1)',
              teks)
KEY, BASE = m.group(1).strip('\'"'), m.group(2)
HDR = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}

PESAN = ('Perbaiki kalimat tesis ini sesuai PUEBI. Balas HANYA kalimat hasil:\n\n'
         'Berdasarkan hasil penelitian yang telah dilaksanakan diatas, '
         'maka dapat ditarik kesimpulan bahwa data yang penulis kumpulkan '
         'adalah tidak signifikan secara statistic.')

body = json.dumps({'model': 'inferhub/cb/deepseek-v4.1-flash',
                   'messages': [{'role': 'user', 'content': PESAN}],
                   'max_tokens': 300}).encode()
req = urllib.request.Request(BASE + '/chat/completions', data=body,
                             headers=HDR, method='POST')
with urllib.request.urlopen(req, timeout=120) as r:
    raw = r.read().decode()
print('Content-Type:', r.headers.get('Content-Type'))
print('PANJANG:', len(raw))
print('── ISI MENTAH (awal 1200) ──')
print(raw[:1200])
print('── ISI MENTAH (akhir 400) ──')
print(raw[-400:])
