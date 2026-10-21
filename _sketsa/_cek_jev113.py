"""Cek: apakah 'typesafe/jev-1.13' & 'jev-latest' ada di daftar model 9router?"""
import subprocess

KODE = r'''
import json, os, urllib.request

base = os.environ.get('EDUAI_ROUTER_BASE', '').rstrip('/')
key = os.environ.get('EDUAI_ROUTER_KEY', '')

req = urllib.request.Request(base + '/models', headers={'Authorization': 'Bearer ' + key})
with urllib.request.urlopen(req, timeout=45) as r:
    d = json.loads(r.read().decode())
ids = [m.get('id') for m in d.get('data', [])]

print('== model typesafe di 9router ==')
for i in ids:
    if i and 'typesafe' in i.lower():
        print('  ', i)
print()
print('== model jev-1.13 / jev-latest ==')
for i in ids:
    if i and ('jev-1' in i.lower() or 'jev-latest' in i.lower()):
        print('  ', i)
print()
print('== hitung ==')
print('  total model :', len(ids))
'''
r = subprocess.run(['docker', 'exec', '-e', 'PYTHONPATH=/app', 'eduai-app',
                    'python3', '-c', KODE], capture_output=True, text=True, timeout=120)
print(r.stdout or r.stderr[-600:])
