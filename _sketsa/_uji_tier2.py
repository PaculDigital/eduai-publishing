"""UJI KANDIDAT TIER 2 - non-DeepSeek, non-Gemini.
Cari: terbaik + cepat + murah + supply banyak.
Kandidat: GLM, Kimi, Qwen, MiniMax (semua keluarga beda dari deepseek/gemini).
max_tokens=8000, temperature=0, 2 putaran.
"""
import json
import statistics
import time
import urllib.error
import urllib.request
from difflib import SequenceMatcher

KEY = open('/opt/data/services/eduai-lab/config/key.txt').read().strip()
BASE = 'https://api.inferhub.dev/v1'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

PESAN = ("Perbaiki ejaan dan tata bahasa paragraf akademik berikut, "
         "jangan ubah makna. Kembalikan HANYA paragraf hasil perbaikan.\n\n"
         "Penelitian ini bertujuan untuk menganalisis pengaruh kualitas kehidupan "
         "kerja terhadap kinerja adaptif pegawai. Kesiapan digital dipakai sebagai "
         "variabel mediasi. Data dikumpulkan memakai kuesioner lima skala likert "
         "yang telah diuji validitas dan reliabilitasnya.")


def panggil(model, max_tokens=8000, temperature=0.0, timeout=240):
    body = json.dumps({
        'model': model,
        'messages': [{'role': 'user', 'content': PESAN}],
        'max_tokens': max_tokens, 'temperature': temperature,
    }).encode()
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
    ch = j['choices'][0]
    c = ch['message'].get('content') or ''
    return {'detik': d, 'model': j.get('model'), 'teks': c, 'panjang': len(c),
            'reasoning': (u.get('completion_tokens_details') or {}).get(
                'reasoning_tokens', 0),
            'finish': ch.get('finish_reason')}, None


# muat harga+supply dari katalog yang sudah diukur
kat = json.load(open('/opt/data/services/eduai-publishing/_katalog_inferhub.json'))
info = {r['id']: r for r in kat['model']}


def harga_supply(mid):
    v = info.get(mid, {})
    return v.get('harga_min'), v.get('supply')


# kandidat Tier 2 - diuji pakai NAMA API (kecil semua), bukan label katalog
KANDIDAT = [
    'ali/glm-5.3', 'ali/glm-5.2',
    'ali/kimi-k2.7-code', 'ali/kimi-k3',
    'ali/qwen3.8-max',
    'cbcn/kimi-k2.7', 'cbcn/kimi-k2.6', 'cbcn/minimax-m3', 'cbcn/minimax-m2.7',
    'cbcn/glm-5.3-flash', 'cbcn/glm-5.3',
    'cb/glm-5.3', 'cb/minimax-m3', 'cb/kimi-k3', 'cb/gpt-5.6-luna',
]

print('=' * 110)
print('UJI KANDIDAT TIER 2 (non-DeepSeek, non-Gemini) — InferHub langsung')
print('=' * 110)

hasil = []
for m in KANDIDAT:
    h, s = harga_supply(m)
    tag = f'min=${h:.4f} supply={s}' if h else 'harga tdk ada di katalog'
    print(f'\n>>> {m}   [{tag}]')
    hs = []
    for ulang in (1, 2):
        r, err = panggil(m)
        if err:
            print(f'    #{ulang}: {err}')
            continue
        print(f"    #{ulang}: {r['detik']:6.1f}s | len={r['panjang']:5d} | "
              f"reason={r['reasoning']:5d} | {r['finish']}")
        if r['panjang'] > 0:
            hs.append(r)
    if hs:
        rata = sum(x['detik'] for x in hs) / len(hs)
        mirip = (SequenceMatcher(None, hs[0]['teks'], hs[1]['teks']).ratio()
                 if len(hs) == 2 else 0.0)
        hasil.append({'model': m, 'ok': len(hs), 'detik': rata,
                      'panjang': sum(x['panjang'] for x in hs) // len(hs),
                      'mirip': mirip, 'harga': h or 999, 'supply': s or 0})
        print(f'    rata {rata:.1f}s | mirip 2 putaran: {mirip:.3f}')
        print(f"    contoh: {hs[0]['teks'][:120]!r}")
    else:
        hasil.append({'model': m, 'ok': 0, 'detik': 0, 'panjang': 0,
                      'mirip': 0.0, 'harga': h or 999, 'supply': s or 0})
        print('    TIDAK ADA JAWABAN')

print('\n' + '=' * 110)
print('RINGKASAN TIER 2 (berhasil dulu, lalu termurah)')
print('=' * 110)
print(f"{'model':26s} {'ok':>3s} {'supply':>7s} {'min$/M':>8s} {'detik':>7s} "
      f"{'len':>5s} {'mirip':>6s}")
for r in sorted(hasil, key=lambda x: (-x['ok'], x['harga'])):
    print(f"{r['model']:26s} {r['ok']:3d} {r['supply']:7d} {r['harga']:8.4f} "
          f"{r['detik']:6.1f}s {r['panjang']:5d} {r['mirip']:6.3f}")

open('/opt/data/services/eduai-publishing/_hasil_tier2.json', 'w').write(
    json.dumps(hasil, ensure_ascii=False, indent=1))
print('\ndisimpan: _hasil_tier2.json')
