#!/usr/bin/env python3
"""Cek: apakah `tab` dari config plugin ikut sampai ke OO (plugins.json)?"""
import gzip
import json
import urllib.request

r = urllib.request.urlopen('http://127.0.0.1/plugins.json')
raw = r.read()
if r.headers.get('Content-Encoding') == 'gzip':
    raw = gzip.decompress(raw)
d = json.loads(raw)

pd = d.get('pluginsData', [])
print('jumlah pluginsData:', len(pd))
print('tipe elemen pertama:', type(pd[0]).__name__ if pd else '-')
print()

for p in pd:
    if isinstance(p, str):
        # mungkin cuma string URL → perlu fetch terpisah
        print('  (string)', p[:80])
        continue
    if not isinstance(p, dict):
        print('  (tipe lain)', type(p).__name__)
        continue
    v = (p.get('variations') or [{}])[0]
    print(f"  {str(p.get('name'))[:24]:26} tab={json.dumps(p.get('tab')):52}"
          f" type={v.get('type')}")

print()
print('=== apakah ada plugin AI di daftar? ===')
for i, p in enumerate(pd):
    if isinstance(p, dict) and str(p.get('name', '')).strip() == 'AI':
        print(f'  index {i}: {json.dumps(p, ensure_ascii=False)[:400]}')
