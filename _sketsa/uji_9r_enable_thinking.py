"""Uji: bisakah `enable_thinking: false` dipasang di JALUR 1 (9router)?

Kalau YA → akar "jalur 1 LAMBAT 180 dtk" (reasoning memakan waktu) ikut
teratasi, bukan cuma jalur 2. Payload = persis _panggil_9router.
"""
import json, os, time, urllib.error, urllib.request

BASE = os.environ['EDUAI_ROUTER_BASE'].rstrip('/')
KEY = os.environ['EDUAI_ROUTER_KEY']
MODEL = os.environ.get('EDUAI_AI_MODEL', 'EduAi')

import sys
sys.path.insert(0, '.')
from app.ai import SYSTEM_REVISI  # noqa: E402

TUGAS = ('NASKAH:\n' + 'Metode penelitian ini menggunakan pendekatan '
         'kuantitatif. ' * 1800 +
         '\n\nKOMENTAR:\n[K1] Kalimat pembuka terlalu umum.\n\n'
         'Balas HANYA dengan:\n[K1-KUTIP-ASLI] <kalimat asli>\n'
         '[K1-GANTI-JADI] <penggantinya>')


def uji(tag, extra, timeout=420):
    p = {'model': MODEL, 'max_tokens': 32000, 'temperature': 0.2,
         'messages': [{'role': 'system', 'content': SYSTEM_REVISI},
                      {'role': 'user', 'content': TUGAS}]}
    p.update(extra)
    req = urllib.request.Request(
        BASE + '/chat/completions', data=json.dumps(p).encode(),
        headers={'Authorization': 'Bearer ' + KEY,
                 'Content-Type': 'application/json'})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            mentah = r.read().decode('utf-8', 'ignore')
        j, _ = json.JSONDecoder().raw_decode(mentah.lstrip())
    except urllib.error.HTTPError as e:
        print(json.dumps({'tag': tag, 'ok': False, 'status': e.code,
                          'galat': e.read().decode('utf-8', 'ignore')[:250]}),
              flush=True)
        return
    except Exception as e:                                   # noqa: BLE001
        print(json.dumps({'tag': tag, 'ok': False,
                          'galat': type(e).__name__ + ': ' + str(e)[:250]}),
              flush=True)
        return
    ch = (j.get('choices') or [{}])[0]
    m = ch.get('message') or {}
    u = j.get('usage') or {}
    print(json.dumps({'tag': tag, 'ok': True,
                      'dt': round(time.monotonic() - t0, 1),
                      'model': j.get('model'),
                      'finish': ch.get('finish_reason'),
                      'content': len(m.get('content') or ''),
                      'reasoning': len(m.get('reasoning_content') or ''),
                      'token_out': u.get('completion_tokens')},
                     ensure_ascii=False), flush=True)


uji('9R-TANPA', {})
time.sleep(1)
uji('9R-DENGAN', {'enable_thinking': False})
