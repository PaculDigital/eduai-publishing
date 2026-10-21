"""UJI SEMUA MODEL DI COMBO EduAi: apakah menerima max_tokens=32.000?

Kenapa penting: kalau SATU model di combo menolak 32.000, fallback bisa MATI
persis saat model utama tumbang — user dapat error, bukan jawaban.
Ini uji "apakah combo tahan 32k", langsung per anggota combo.
"""
import json
import os
import time
import urllib.error
import urllib.request

BASE = os.getenv('EDUAI_ROUTER_BASE', 'http://172.17.0.1:20128/v1')
KEY = os.getenv('EDUAI_ROUTER_KEY', '')

ANGGOTA = [
    ('inferhub/ali/deepseek-v4.1-flash', 'slot 1 — utama'),
    ('inferhub/cbcn/deepseek-v4.1-flash', 'slot 2'),
    ('inferhub/ag/gemini-3.7-flash-high', 'slot 3'),
    ('inferhub/cbcn/deepseek-v4-flash', 'slot 4'),
    ('inferhub/cbcn/glm-5.3-flash', 'slot 5 — NON-REASONING'),
]

PESAN = ("Perbaiki ejaan kalimat ini: penelitian ini bertujuan untuk "
         "menganalisis pengaruh kualitas kehidupan kerja terhadap kinerja.")


def panggil(model, max_tokens):
    body = json.dumps({'model': model,
                       'messages': [{'role': 'user', 'content': PESAN}],
                       'max_tokens': max_tokens, 'temperature': 0.2}).encode()
    req = urllib.request.Request(
        f'{BASE}/chat/completions', data=body,
        headers={'Authorization': f'Bearer {KEY}',
                 'Content-Type': 'application/json'})
    t0 = time.monotonic()
    try:
        resp = urllib.request.urlopen(req, timeout=300)
        raw = resp.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return None, f'HTTP {e.code}: {e.read().decode("utf-8","ignore")[:170]}'
    except Exception as e:
        return None, f'ERROR {type(e).__name__}: {e}'
    d = time.monotonic() - t0
    i = raw.find('data: [DONE]')
    try:
        j = json.JSONDecoder().raw_decode(raw[:i] if i > 0 else raw)[0]
    except Exception as e:
        return None, f'PARSE {e}'
    u = j.get('usage') or {}
    ch = j['choices'][0]
    rt = (u.get('completion_tokens_details') or {}).get('reasoning_tokens', 0)
    return {'detik': d, 'model': j.get('model'), 'len': len(ch['message'].get('content') or ''),
            'reasoning': rt, 'out': u.get('completion_tokens'),
            'finish': ch.get('finish_reason')}, None


print('=' * 100)
print('UJI TOLERANSI max_tokens=32.000 PER ANGGOTA COMBO')
print('=' * 100)
for m, ket in ANGGOTA:
    print(f'\n>>> {m}  [{ket}]')
    for mt in (32000, 128000):
        r, err = panggil(m, mt)
        if err:
            print(f'    max_tokens={mt:>7,}  ❌ {err}')
        else:
            status = 'OK' if r['len'] > 0 else 'KOSONG'
            print(f"    max_tokens={mt:>7,}  ✅ {r['detik']:5.1f}s | "
                  f"len={r['len']:4d} | reason={r['reasoning']:5d} | "
                  f"out={r['out']:5d} | {r['finish']} | {status}")