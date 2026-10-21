"""UJI COMBO YANG BARU DIBUAT: eduai-tier-1 dan eduai-tier-2.
Panggil pakai nama combo (bukan nama model) + 2 putaran tiap combo.
"""
import json
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
        return None, f'HTTP {e.code}: {e.read().decode("utf-8","ignore")[:150]}'
    except Exception as e:
        return None, f'ERROR {type(e).__name__}: {e}'
    d = time.monotonic() - t0
    i = raw.find('data: [DONE]')
    try:
        j = json.JSONDecoder().raw_decode(raw[:i] if i > 0 else raw)[0]
    except Exception as e:
        return None, f'PARSE {e}'
    ch = j['choices'][0]
    c = ch['message'].get('content') or ''
    return {'detik': d, 'model_dipakai': j.get('model'), 'teks': c,
            'panjang': len(c), 'finish': ch.get('finish_reason')}, None


print('=' * 104)
print('UJI COMBO BARU — dipanggil PAKAI NAMA COMBO')
print('=' * 104)
for combo in ('combo/eduai-tier-1', 'combo/eduai-tier-2'):
    print(f'\n>>> {combo}')
    hs = []
    for ulang in (1, 2):
        r, err = panggil(combo)
        if err:
            print(f'    #{ulang}: ❌ {err}')
            continue
        print(f"    #{ulang}: {r['detik']:6.1f}s | model_dipakai={r['model_dipakai']} "
              f"| len={r['panjang']} | {r['finish']}")
        if r['panjang'] > 0:
            hs.append(r)
    if len(hs) == 2:
        mirip = SequenceMatcher(None, hs[0]['teks'], hs[1]['teks']).ratio()
        print(f'    ✅ 2/2 BERHASIL | rata {sum(x["detik"] for x in hs)/2:.1f}s '
              f'| kemiripan: {mirip:.3f}')
        print(f"    contoh: {hs[0]['teks'][:200]!r}")
    elif hs:
        print(f'    ⚠️ hanya {len(hs)}/2 berhasil')
    else:
        print('    ❌ COMBO TIDAK BEKERJA')

# daftar ulang combo
print('\n' + '=' * 104)
print('DAFTAR COMBO EDUAI DI AKUN')
print('=' * 104)
req = urllib.request.Request('https://inferhub.dev/api/combos',
                             headers={'Authorization': f'Bearer {KEY}',
                                      'User-Agent': UA})
for c in json.loads(urllib.request.urlopen(req, timeout=60).read().decode()):
    if 'eduai' in c['slug']:
        print(f"\n  {c['name']}  (combo/{c['slug']})")
        print(f"    selection={c.get('selection')} sticky={c.get('sticky')} "
              f"maxTtftMs={c.get('maxTtftMs')}")
        print(f"    id={c.get('id')}")
        for m in c.get('members', []):
            print(f"      - {m.get('model')}")
