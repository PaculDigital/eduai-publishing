"""UJI: panggil JEV lewat 9router (bukan langsung ke OpenRouter)."""
import subprocess

KODE = r'''
import json, os, urllib.request, urllib.error, time

base = os.environ.get('EDUAI_ROUTER_BASE', '').rstrip('/')
key = os.environ.get('EDUAI_ROUTER_KEY', '')

STATE = ("BAB I PENDAHULUAN\nLatar belakang masalah.\n"
         "BAB II TINJAUAN PUSTAKA\nTeori pendukung.\n"
         "BAB III METODE PENELITIAN\nCara penelitian.")

def panggil(model, body, label):
    t0 = time.time()
    req = urllib.request.Request(base + '/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            isi = r.read().decode()
            print(f'[{label}] HTTP {r.status} OK ({time.time()-t0:.2f} dtk)')
            print(isi[:900])
    except urllib.error.HTTPError as e:
        print(f'[{label}] HTTP {e.code} ({time.time()-t0:.2f} dtk)')
        print(e.read().decode()[:700])
    except Exception as e:
        print(f'[{label}] GAGAL {type(e).__name__}: {e}')
    print()

# A: cara BIASA (chat) -> diperkirakan ditolak
panggil('JEV/typesafe/jev-router',
        {'model': 'JEV/typesafe/jev-router',
         'messages': [{'role': 'user', 'content': 'Halo'}]},
        'A: JEV/typesafe/jev-router via chat')

# B: model lain lewat provider JEV (bukti jalur hidup)
panggil('JEV/deepseek/deepseek-v4.1-flash',
        {'model': 'JEV/deepseek/deepseek-v4.1-flash',
         'messages': [{'role': 'user', 'content': 'Balas satu kata: OK'}]},
        'B: JEV/deepseek-v4.1-flash (uji jalur hidup)')
'''
r = subprocess.run(['docker', 'exec', '-e', 'PYTHONPATH=/app', 'eduai-app',
                    'python3', '-c', KODE], capture_output=True, text=True, timeout=180)
print(r.stdout or r.stderr[-900:])
