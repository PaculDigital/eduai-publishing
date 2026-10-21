#!/usr/bin/env python3
"""PROBE LATENSI A/B — inferhub vs Byn, soal sama, 3 run per model.

Permintaan Bos 13Sep26: cepat mana inferhub vs Byn?
"""
import json, re, time, statistics, urllib.request

BASE = 'http://172.17.0.1:20128/v1'

def api_key():
    t = open('/opt/data/config.yaml').read()
    m = re.search(r'api_key:\s*([^\s]+)\s*\n\s*base_url:\s*(http://172\.17\.0\.1:20128/v1)', t)
    return m.group(1).strip('"\'')

SOAL = ('Perbaiki kalimat ini sesuai PUEBI. Jawab HANYA kalimat hasilnya, tanpa penjelasan: '
        '"hasil penelitian nya menunjukkan bahwa dia merubah pendekatannya"')
HARUS = ['penelitiannya', 'mengubah']

def tanya(model, timeout=90):
    req = urllib.request.Request(
        f'{BASE}/chat/completions',
        data=json.dumps({'model': model, 'messages': [{'role': 'user', 'content': SOAL}],
                         'max_tokens': 2000}).encode(),
        headers={'Authorization': f'Bearer {api_key()}', 'Content-Type': 'application/json'})
    t0 = time.time()
    try:
        raw = urllib.request.urlopen(req, timeout=timeout).read().decode()
        i = raw.find('data: [DONE]')
        j = json.JSONDecoder().raw_decode(raw[:i] if i > 0 else raw)[0]
        c = j['choices'][0]['message']['content']
        return time.time() - t0, ('✅' if all(h in c for h in HARUS) else '⚠️'), c
    except Exception as e:
        return time.time() - t0, '❌', str(e)[:80]

MODELS = [
    'inferhub/ag/gemini-3.8-flash-high',
    'Byn/gemini-3.8-flash-high',
    'inferhub/deepseek-v4.1-flash',
    'Byn/deepseek-v4.1-flash',
]
RUN = 3
hasil = {}
for mo in MODELS:
    dts, oks = [], []
    for _ in range(RUN):
        dtk, ok, c = tanya(mo)
        dts.append(dtk); oks.append(ok)
        print(f'  {mo:38} {ok} {dtk:5.1f}s')
        if ok == '❌':
            break
    if dts and oks[-1] != '❌':
        hasil[mo] = {'median': round(statistics.median(dts), 1),
                     'min': round(min(dts), 1),
                     'benar': f"{oks.count('✅')}/{len(oks)}"}

print()
print(f'{"MODEL":<38} {"MEDIAN":>7} {"MIN":>6}  BENAR')
for mo, h in hasil.items():
    print(f'{mo:<38} {h["median"]:>6}s {h["min"]:>5}s  {h["benar"]}')
json.dump(hasil, open('/opt/data/services/eduai-publishing/scripts/hasil_latensi_ab.json', 'w'), indent=1)
