#!/usr/bin/env python3
"""PROBE FALLBACK — uji apakah model provider selain inferhub benar-benar jalan.

Kandidat fallback produksi EduAi (permintaan Bos 13Sep26): jangan 1 provider.
Probe: 1 kalimat PUEBI kecil per model, ukur waktu + kebenaran dasar.
"""
import json, re, time, urllib.request, urllib.error

BASE = 'http://172.17.0.1:20128/v1'

def api_key():
    t = open('/opt/data/config.yaml').read()
    m = re.search(r'api_key:\s*([^\s]+)\s*\n\s*base_url:\s*(http://172\.17\.0\.1:20128/v1)', t)
    return m.group(1).strip('"\'')

def tanya(model, pertanyaan, max_tokens=2000, timeout=90):
    req = urllib.request.Request(
        f'{BASE}/chat/completions',
        data=json.dumps({'model': model, 'messages': [
            {'role': 'user', 'content': pertanyaan}], 'max_tokens': max_tokens}).encode(),
        headers={'Authorization': f'Bearer {api_key()}', 'Content-Type': 'application/json'})
    t0 = time.time()
    try:
        raw = urllib.request.urlopen(req, timeout=timeout).read().decode()
        i = raw.find('data: [DONE]')
        body = raw[:i] if i > 0 else raw
        j = json.JSONDecoder().raw_decode(body)[0]
        return time.time() - t0, j['choices'][0]['message']['content']
    except Exception as e:
        return time.time() - t0, f'ERROR: {str(e)[:150]}'

SOAL = ('Perbaiki kalimat ini sesuai PUEBI. Jawab HANYA kalimat hasilnya, tanpa penjelasan: '
        '"hasil penelitian nya menunjukkan bahwa dia merubah pendekatannya"')
HARUS = ['penelitiannya', 'mengubah']  # penanda benar

kandidat = [
    'Byn/gemini-3.8-flash-high',
    'Byn/deepseek-v4.1-flash',
    'Byn/glm-5.3',
    'cf/gemini-3.8-flash-high',
]
for mo in kandidat:
    dtk, jawab = tanya(mo, SOAL)
    if jawab.startswith('ERROR'):
        print(f'{mo:36} ❌ {dtk:5.1f}s {jawab[:90]}')
        continue
    ok = all(h in jawab for h in HARUS)
    print(f'{mo:36} {"✅" if ok else "⚠️"} {dtk:5.1f}s {jawab[:80]!r}')
