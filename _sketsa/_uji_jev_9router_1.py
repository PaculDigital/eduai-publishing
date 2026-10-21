"""UJI: apakah model JEV bisa dipanggil LEWAT 9router (bukan langsung)?"""
import json
import os
import subprocess
import urllib.error
import urllib.request

# cek daftar model 9router dari sisi container EduAi (yang tersambung)
KODE = r'''
import json, os, urllib.request
base = os.environ.get('EDUAI_ROUTER_BASE', '')
key = os.environ.get('EDUAI_ROUTER_KEY', '')
print('base:', base)
req = urllib.request.Request(base.rstrip('/') + '/models',
                             headers={'Authorization': 'Bearer ' + key})
with urllib.request.urlopen(req, timeout=45) as r:
    d = json.loads(r.read().decode())
ids = [m.get('id') for m in d.get('data', [])]
print('total model:', len(ids))
jev = [i for i in ids if 'jev' in (i or '').lower() or 'JEV' in (i or '')]
print('model JEV:', jev)
'''
r = subprocess.run(['docker', 'exec', '-e', 'PYTHONPATH=/app', 'eduai-app',
                    'python3', '-c', KODE], capture_output=True, text=True, timeout=120)
print('--- daftar model 9router ---')
print(r.stdout or r.stderr[-500:])
