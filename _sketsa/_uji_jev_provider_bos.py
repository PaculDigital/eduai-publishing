"""UJI: panggil Jev lewat provider "JEV" yang Bos buat (defaultModel=jev-1.13).

Kita tahu /chat/completions akan DITOLAK untuk jev-1.13. Uji ini untuk
MEMBUKTIKAN dengan pesan apa 9router menolaknya (kalau ditolak).
"""
import subprocess

KODE = r'''
import json, os, urllib.request, urllib.error, time

base = os.environ.get('EDUAI_ROUTER_BASE', '').rstrip('/')
key = os.environ.get('EDUAI_ROUTER_KEY', '')

def panggil(model, label, extra=None):
    body = {'model': model, 'messages': [{'role': 'user', 'content': 'Halo'}]}
    if extra:
        body.update(extra)
    t0 = time.time()
    req = urllib.request.Request(base + '/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            isi = r.read().decode()
            print(f'[{label}] HTTP {r.status} ({time.time()-t0:.2f} dtk)')
            print('  ', isi[:600].replace('\n', ' '))
    except urllib.error.HTTPError as e:
        print(f'[{label}] HTTP {e.code} ({time.time()-t0:.2f} dtk)')
        print('  ', e.read().decode()[:600].replace('\n', ' '))
    except Exception as e:
        print(f'[{label}] GAGAL {type(e).__name__}: {e}')
    print()

panggil('JEV', 'JEV (defaultModel = jev-1.13)')
panggil('JEV/typesafe/jev-1.13', 'JEV/typesafe/jev-1.13')
panggil('typesafe/jev-1.13', 'typesafe/jev-1.13 polos')
'''
r = subprocess.run(['docker', 'exec', '-e', 'PYTHONPATH=/app', 'eduai-app',
                    'python3', '-c', KODE], capture_output=True, text=True, timeout=180)
print(r.stdout or r.stderr[-600:])
