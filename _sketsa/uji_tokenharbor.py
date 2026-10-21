"""Uji TokenHarbor.ai: sehat? cepat? patuh format? — sebelum disambung."""
import json
import time
import urllib.request

BASE = 'https://tokenharbor.ai/v1'
KEY = 'thk_live_XXX'  # diganti saat jalan: baca dari argumen stdin

import sys
KEY = sys.argv[1] if len(sys.argv) > 1 else ''

for model in ['mimo-v2.6-flash', 'glm-5.3-flash']:
    isi = json.dumps({
        'model': model,
        'messages': [
            {'role': 'user',
             'content': 'Balas HANYA: "Siap, EduAi siap membantu."'},
        ],
        'max_tokens': 60,
    }).encode()
    req = urllib.request.Request(BASE + '/chat/completions', data=isi)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {KEY}')
    t0 = time.time()
    try:
        d = urllib.request.urlopen(req, timeout=90)
        j = json.loads(d.read().decode())
        dt = time.time() - t0
        isi = j['choices'][0]['message'].get('content', '')
        print(f'{model}: OK {dt:.1f} dtk · {len(isi)} kar · '
              f'"{isi[:60]}"')
    except Exception as e:
        print(f'{model}: GAGAL {time.time()-t0:.1f} dtk — {e}')
        try:
            print('   isi galat:', str(e.read())[:200])
        except Exception:
            pass
