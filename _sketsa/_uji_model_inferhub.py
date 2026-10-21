"""UJI ULANG 'MODEL DIAM' - LANGSUNG ke InferHub (bukan lewat 9router).
Pakai urllib (httpx tidak ada di container hermes).
"""
import json
import time
import urllib.error
import urllib.request

KEY = open('/opt/data/services/eduai-lab/config/key.txt').read().strip()
BASE = 'https://api.inferhub.dev/v1'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

PESAN = ("Perbaiki ejaan paragraf ini, jangan ubah makna:\n\n"
         "Penelitian ini bertujuan untuk menganalisis pengaruh kualitas kehidupan "
         "kerja terhadap kinerja adaptif pegawai. Kesiapan digital dipakai sebagai "
         "variabel mediasi. Data dikumpulkan memakai kuesioner lima skala likert.")


def panggil(model, max_tokens, temperature=0.0):
    body = json.dumps({
        'model': model,
        'messages': [{'role': 'user', 'content': PESAN}],
        'max_tokens': max_tokens,
        'temperature': temperature,
    }).encode()
    req = urllib.request.Request(
        f'{BASE}/chat/completions', data=body,
        headers={'Authorization': f'Bearer {KEY}',
                 'Content-Type': 'application/json',
                 'User-Agent': UA})
    t0 = time.monotonic()
    try:
        resp = urllib.request.urlopen(req, timeout=300)
        kode, raw = resp.status, resp.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return f'HTTP {e.code}: {e.read().decode("utf-8", "ignore")[:200]}'
    except Exception as e:
        return f'ERROR {type(e).__name__}: {e}'
    d = time.monotonic() - t0

    i = raw.find('data: [DONE]')
    body2 = raw[:i] if i > 0 else raw
    try:
        j = json.JSONDecoder().raw_decode(body2)[0]
    except Exception as e:
        return f'PARSE ERROR {e} | raw[:250]={raw[:250]!r}'

    u = j.get('usage') or {}
    rt = (u.get('completion_tokens_details') or {}).get('reasoning_tokens', 0)
    ch = j['choices'][0]
    c = ch['message'].get('content') or ''
    return (f'{d:6.1f}s | model={j.get("model")} | len={len(c)} | '
            f'reasoning={rt} | completion={u.get("completion_tokens")} | '
            f'finish={ch.get("finish_reason")} | max_tokens={max_tokens}')


UJI = [
    ('cb/deepseek-v4.1-flash', 1500),
    ('cb/deepseek-v4.1-flash', 8000),
    ('cb/deepseek-v4.1-flash', 24000),
    ('cbcn/deepseek-v4-flash', 1500),
    ('cbcn/deepseek-v4-flash', 8000),
    ('ag/gemini-3.8-flash-high', 1500),
]

print('=' * 100)
print('UJI ULANG LANGSUNG KE INFERHUB - max_tokens DIPERBESAR')
print('=' * 100)
for m, mt in UJI:
    print(f'\n>>> {m}  (max_tokens={mt})')
    for ulang in (1, 2):
        print(f'    #{ulang}: {panggil(m, mt)}')
