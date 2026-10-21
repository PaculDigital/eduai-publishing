"""UJI COMBO EduAi LEWAT 9router (jalur produksi), setelah urutan diubah.
4 panggilan: lihat model mana yang benar-benar dipakai + apakah jawaban kosong."""
import json
import os
import time
import urllib.error
import urllib.request

BASE = os.getenv('EDUAI_ROUTER_BASE', 'http://172.17.0.1:20128/v1')
KEY = os.getenv('EDUAI_ROUTER_KEY', '')
MODEL = os.getenv('EDUAI_AI_MODEL', 'EduAi')

PESAN = ("Perbaiki ejaan paragraf akademik berikut, jangan ubah makna. "
         "Kembalikan HANYA paragraf hasil perbaikan.\n\n"
         "Penelitian ini bertujuan untuk menganalisis pengaruh kualitas kehidupan "
         "kerja terhadap kinerja adaptif pegawai. Kesiapan digital dipakai sebagai "
         "variabel mediasi. Data dikumpulkan memakai kuesioner lima skala likert.")


def panggil():
    body = json.dumps({'model': MODEL,
                       'messages': [{'role': 'user', 'content': PESAN}],
                       'max_tokens': 8000, 'temperature': 0.2}).encode()
    req = urllib.request.Request(
        f'{BASE}/chat/completions', data=body,
        headers={'Authorization': f'Bearer {KEY}',
                 'Content-Type': 'application/json'})
    t0 = time.monotonic()
    try:
        resp = urllib.request.urlopen(req, timeout=420)
        raw = resp.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return None, f'HTTP {e.code}: {e.read().decode("utf-8","ignore")[:150]}'
    except Exception as e:
        return None, f'ERROR {type(e).__name__}: {e}'
    d = time.monotonic() - t0
    i = raw.find('data: [DONE]')
    try:
        j = json.JSONDecoder().raw_decode(raw[:i] if i > 0 else raw)[0]
    except Exception as e:
        return None, f'PARSE {e} | {raw[:200]!r}'
    u = j.get('usage') or {}
    rt = (u.get('completion_tokens_details') or {}).get('reasoning_tokens', 0)
    ch = j['choices'][0]
    c = ch['message'].get('content') or ''
    return {'detik': d, 'model': j.get('model'), 'len': len(c),
            'reasoning': rt, 'out': u.get('completion_tokens'),
            'finish': ch.get('finish_reason'), 'teks': c}, None


print('=' * 96)
print(f'UJI COMBO "{MODEL}" LEWAT 9router (jalur produksi) — 4 panggilan')
print('=' * 96)
for n in range(1, 5):
    r, err = panggil()
    if err:
        print(f'#{n}: ❌ {err}')
        continue
    status = '✅' if r['len'] > 0 else '❌ KOSONG'
    print(f"#{n}: {r['detik']:6.1f}s | model={r['model']} | len={r['len']} "
          f"| reason={r['reasoning']} | out={r['out']} | {r['finish']} {status}")
    if n == 1 and r['len']:
        print(f"    contoh: {r['teks'][:170]!r}")
