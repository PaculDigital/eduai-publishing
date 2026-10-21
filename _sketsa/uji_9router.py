import json
import subprocess
import time
import urllib.request

# ambil kunci router dari env container
env = subprocess.run(
    ['docker', 'exec', 'eduai-app', 'env'], capture_output=True,
    text=True).stdout
kunci = ''
for baris in env.splitlines():
    if 'ROUTER' in baris.upper() and '=' in baris:
        k, v = baris.split('=', 1)
        if 'KEY' in k.upper() or 'TOKEN' in k.upper():
            kunci = v
            print('pakai env:', k)
            break
if not kunci:
    print('TIDAK KETEMU env kunci — daftar env router-ish:')
    for b in env.splitlines():
        if 'ROUT' in b.upper() or '9R' in b:
            print(' ', b[:40])
    raise SystemExit(1)

isi = json.dumps({
    'model': 'EduAi',
    'messages': [{'role': 'user', 'content': 'Balas singkat: siap'}],
    'max_tokens': 20,
}).encode()
req = urllib.request.Request(
    'http://172.17.0.1:20128/v1/chat/completions', data=isi)
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', f'Bearer {kunci}')
t0 = time.time()
try:
    d = urllib.request.urlopen(req, timeout=90)
    balasan = d.read().decode()
    dt = time.time() - t0
    print(f'OK {dt:.1f} dtk — mentah: {balasan[:250]}')
except Exception as e:
    print(f'GAGAL {time.time()-t0:.1f} dtk: {e}')
