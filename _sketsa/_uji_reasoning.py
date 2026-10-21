"""PISAHKAN MODEL REASONING vs NON-REASONING — berbasis BUKTI, bukan teori.

Cara ukur: kirim prompt SEDERHANA, lihat apakah ada `reasoning_tokens` > 0
di usage. Kalau reasoning_tokens terisi = model reasoning.
Kalau 0 / tidak ada = non-reasoning (jawaban langsung).

max_tokens=8000 (seperti produksi), temperature=0.
"""
import json
import statistics
import time
import urllib.error
import urllib.request

KEY = open('/opt/data/services/eduai-lab/config/key.txt').read().strip()
BASE = 'https://api.inferhub.dev/v1'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

PESAN = "Balas satu kalimat saja: apa itu metodologi penelitian?"


def panggil(model, max_tokens=8000, timeout=240):
    body = json.dumps({'model': model,
                       'messages': [{'role': 'user', 'content': PESAN}],
                       'max_tokens': max_tokens, 'temperature': 0.0}).encode()
    req = urllib.request.Request(
        f'{BASE}/chat/completions', data=body,
        headers={'Authorization': f'Bearer {KEY}',
                 'Content-Type': 'application/json', 'User-Agent': UA})
    t0 = time.monotonic()
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        raw = resp.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return None, f'HTTP {e.code}: {e.read().decode("utf-8","ignore")[:110]}'
    except Exception as e:
        return None, f'ERROR {type(e).__name__}: {e}'
    d = time.monotonic() - t0
    i = raw.find('data: [DONE]')
    try:
        j = json.JSONDecoder().raw_decode(raw[:i] if i > 0 else raw)[0]
    except Exception as e:
        return None, f'PARSE {e}'
    u = j.get('usage') or {}
    det = u.get('completion_tokens_details') or {}
    ch = j['choices'][0]
    c = ch['message'].get('content') or ''
    return {'detik': d, 'reasoning': det.get('reasoning_tokens'),
            'detail_ada': bool(det), 'usage': u, 'panjang': len(c),
            'finish': ch.get('finish_reason'), 'teks': c,
            'model': j.get('model')}, None


# Semua model yang relevan (tier 1, tier 2, dan pembanding)
MODELS = [
    # TIER 1 (pilihan Bos)
    'ali/deepseek-v4.1-flash',
    'ag/gemini-3.7-flash-high',
    'cbcn/deepseek-v4.1-flash',
    # TIER 2
    'ali/kimi-k2.7-code',
    'ali/qwen3.8-max',
    'cbcn/glm-5.3-flash',
    # pembanding yang sempat muncul
    'cb/deepseek-v4.1-flash',
    'cb/gpt-5.6-luna',
    'zai/glm-5.3-flash',
    'cb/gemini-3.1-pro',
    'ag/gemini-3.8-flash-high',
]

print('=' * 106)
print('UKUR REASONING TOKEN — pemisah model BERPIKIR vs LANGSUNG MENJAWAB')
print('=' * 106)

hasil = []
for m in MODELS:
    r, err = panggil(m)
    if err:
        print(f'\n>>> {m}\n    ❌ {err}')
        hasil.append({'model': m, 'reasoning': None, 'detik': 0, 'panjang': 0,
                      'finish': '-', 'err': err})
        continue
    rt = r['reasoning']
    jenis = ('REASONING' if (rt or 0) > 0 else 'NON-REASONING'
             if rt == 0 else 'TIDAK DIKETAHUI')
    print(f"\n>>> {m}")
    print(f"    {r['detik']:6.1f}s | reasoning_tokens={rt} | "
          f"detail_ada={r['detail_ada']} | len={r['panjang']} | {r['finish']}")
    print(f"    usage mentah: {json.dumps(r['usage'])}")
    print(f"    → {jenis}")
    hasil.append({'model': m, 'reasoning': rt, 'detik': r['detik'],
                  'panjang': r['panjang'], 'finish': r['finish'], 'err': None})

print('\n' + '=' * 106)
print('TABEL PEMISAH')
print('=' * 106)
print(f"{'model':30s} {'reasoning_tok':>13s} {'JENIS':>14s} {'detik':>7s} {'len':>5s}")
for r in hasil:
    if r['err']:
        print(f"{r['model']:30s} {'-':>13s} {'GAGAL':>14s} {'-':>7s} {'-':>5s}")
    else:
        rt = r['reasoning']
        jenis = ('REASONING' if (rt or 0) > 0
                 else 'NON-REASONING' if rt == 0 else 'TIDAK DIKETAHUI')
        print(f"{r['model']:30s} {str(rt):>13s} {jenis:>14s} "
              f"{r['detik']:6.1f}s {r['panjang']:5d}")

open('/opt/data/services/eduai-publishing/_hasil_reasoning.json', 'w').write(
    json.dumps(hasil, ensure_ascii=False, indent=1))
print('\ndisimpan: _hasil_reasoning.json')
