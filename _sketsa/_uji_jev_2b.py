"""UJI 2b: bentuk systemone yang BENAR (questions punya 'instructions')."""
import json
import sqlite3
import urllib.request
import urllib.error

c = sqlite3.connect('/tmp/9router_cek/data.sqlite')
c.row_factory = sqlite3.Row
row = c.execute("select data from providerConnections where provider='openrouter'").fetchone()
key = json.loads(dict(row)['data']).get('apiKey')


def kirim(body, label, url='https://openrouter.ai/api/v1/systemone'):
    import time
    t0 = time.time()
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
        'Authorization': 'Bearer ' + key,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://eduai.local',
        'X-Title': 'EduAi Satpam Test',
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            isi = r.read().decode()
            print(f'[{label}] HTTP {r.status} ✅ ({time.time()-t0:.2f} detik)')
            print(isi[:1200])
    except urllib.error.HTTPError as e:
        print(f'[{label}] HTTP {e.code} ❌ ({time.time()-t0:.2f} detik)')
        print(e.read().decode()[:700])
    except Exception as e:
        print(f'[{label}] GAGAL: {type(e).__name__} {e}')
    print()


STATE = ("BAB I PENDAHULUAN\nBab ini membahas latar belakang masalah.\n"
         "BAB II TINJAUAN PUSTAKA\nBab ini membahas teori.\n"
         "BAB III METODE PENELITIAN\nBab ini membahas cara penelitian.")

# bentuk A: instructions sebagai STRING di dalam question
kirim({
    'model': 'typesafe/jev-1.13',
    'state': STATE,
    'questions': {
        'berurutan': {'instructions': 'Apakah bab-bab ini berurutan I, II, III?',
                      'type': 'noul'},
    },
}, 'A: instructions string + type noul')

# bentuk B: instructions + options eksplisit
kirim({
    'model': 'typesafe/jev-1.13',
    'state': STATE,
    'questions': {
        'struktur': {'instructions': 'Apakah struktur bab ini lengkap?',
                     'type': 'noul'},
        'kategori': {'instructions': 'Bagian ini termasuk kategori apa?',
                     'type': 'choice',
                     'options': ['pendahuluan', 'tinjauan', 'metode', 'hasil']},
    },
}, 'B: 2 pertanyaan sekaligus (noul + choice)')
