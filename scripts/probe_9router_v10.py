#!/usr/bin/env python3
"""PROBE v10 — bukti JSON telanjang berisi jawaban (parse langsung)."""
import json
import re
import urllib.request

teks = open('/opt/data/config.yaml').read()
m = re.search(r'api_key:\s*([^\s]+)\s*\n\s*base_url:\s*(http://172\.17\.0\.1:20128/v1)',
              teks)
KEY, BASE = m.group(1).strip('\'"'), m.group(2)
HDR = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}

PESAN = ('Perbaiki kalimat tesis berikut sesuai PUEBI. Balas HANYA kalimat hasil:\n\n'
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
# JSON objek pertama + kemungkinan trailing (data: [DONE] dll)
d, _pakai = json.JSONDecoder().raw_decode(raw.lstrip())
msg = d['choices'][0]['message']
print('finish_reason :', d['choices'][0].get('finish_reason'))
print('content       :', repr(msg.get('content')))
print('sisa trailing :', repr(raw.lstrip()[_pakai:][:80]))
