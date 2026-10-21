"""Cek bentuk endpoint /api/alpha/decisions (yang OpenRouter sebut).

Kita tahu /v1/systemone BEKERJA. Sekarang cek apakah /api/alpha/decisions
ada, dan bentuk kirimannya sama atau beda.
"""
import json
import sqlite3
import time
import urllib.error
import urllib.request

c = sqlite3.connect('/tmp/9router_cek2/data.sqlite')
c.row_factory = sqlite3.Row
KEY = json.loads(dict(c.execute(
    "select data from providerConnections where name='JEV'").fetchone())['data'])['apiKey']
print('kunci JEV: ADA, panjang', len(KEY))

STATE = ("BAB I PENDAHULUAN\nLatar belakang.\nBAB II TINJAUAN PUSTAKA\nTeori.\n"
         "BAB III METODE PENELITIAN\nCara.")
Q = {'berurutan': {'instructions': 'Apakah bab berurutan I, II, III?', 'type': 'noul'}}


def coba(url, body, label):
    t0 = time.time()
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
        headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json',
                 'HTTP-Referer': 'https://eduai.local', 'X-Title': 'EduAi Satpam'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            print(f'[{label}] HTTP {r.status} ✅ ({time.time()-t0:.2f} dtk)')
            print('  ', r.read().decode()[:500].replace('\n', ' '))
    except urllib.error.HTTPError as e:
        print(f'[{label}] HTTP {e.code} ({time.time()-t0:.2f} dtk)')
        print('  ', e.read().decode()[:500].replace('\n', ' '))
    except Exception as e:
        print(f'[{label}] GAGAL {type(e).__name__}: {e}')
    print()


# 1. endpoint yang OpenRouter sebut
coba('https://openrouter.ai/api/alpha/decisions',
     {'model': 'typesafe/jev-1.13', 'state': STATE, 'questions': Q},
     'A: api/alpha/decisions')

# 2. versi v1
coba('https://openrouter.ai/api/v1/alpha/decisions',
     {'model': 'typesafe/jev-1.13', 'state': STATE, 'questions': Q},
     'B: api/v1/alpha/decisions')

# 3. systemone (yang sudah terbukti)
coba('https://openrouter.ai/api/v1/systemone',
     {'model': 'typesafe/jev-1.13', 'state': STATE, 'questions': Q},
     'C: api/v1/systemone (sudah terbukti)')
