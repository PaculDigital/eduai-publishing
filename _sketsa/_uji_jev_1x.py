"""UJI 1 permintaan ke OpenRouter: apakah kunci Bos bisa memanggil Jev?
Hanya MEMBACA pesan galat/penerimaan — tidak mengubah apa pun.
"""
import json
import sqlite3
import urllib.request
import urllib.error

# ambil kunci dari SALINAN DB 9router (tidak dicetak)
c = sqlite3.connect('/tmp/9router_cek/data.sqlite')
c.row_factory = sqlite3.Row
row = c.execute("select data from providerConnections where provider='openrouter'").fetchone()
key = json.loads(dict(row)['data']).get('apiKey')
print('kunci:', 'ADA' if key else 'TIDAK ADA', '| panjang:', len(key or ''))

def kirim(url, body, label):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={
        'Authorization': 'Bearer ' + key,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://eduai.local',
        'X-Title': 'EduAi Satpam Test',
    })
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            print(f'[{label}] HTTP {r.status} ✅')
            print(r.read().decode()[:900])
    except urllib.error.HTTPError as e:
        print(f'[{label}] HTTP {e.code} ❌')
        print(e.read().decode()[:900])
    except Exception as e:
        print(f'[{label}] GAGAL: {type(e).__name__} {e}')

# UJI 1: cara BIASA (chat/completions) — kita TAHU ini ditolak
kirim('https://openrouter.ai/api/v1/chat/completions',
      {'model': 'typesafe/jev-1.13',
       'messages': [{'role': 'user', 'content': 'hello'}]},
      'chat/completions (cara biasa)')

print()

# UJI 2: cara KHUSUS Jev (systemone) — inilah yang harus diuji
kirim('https://openrouter.ai/api/v1/systemone',
      {'model': 'typesafe/jev-1.13',
       'state': 'BAB I PENDAHULUAN\nBAB II TINJAUAN PUSTAKA\nBAB III METODE PENELITIAN',
       'questions': {'berurutan': {'type': 'noul'}}},
      'systemone (cara khusus Jev)')
