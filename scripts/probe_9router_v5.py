#!/usr/bin/env python3
"""PROBE 9router v5 — cari model CEPAT utk revisi teks (uji 5 model flash/gemini).

Uji: 1 prompt revisi kecil akademik → ukur waktu + kualitas jawaban.
Output: tabel perbandingan.
"""
import json
import re
import time
import urllib.request

teks = open('/opt/data/config.yaml').read()
m = re.search(r'api_key:\s*([^\s]+)\s*\n\s*base_url:\s*(http://172\.17\.0\.1:20128/v1)',
              teks)
KEY, BASE = m.group(1).strip('\'"'), m.group(2)
HDR = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}


def tanya(model, pesan, max_tokens=300):
    """Kirim chat, kumpulkan stream SSE → teks final. Return (teks, detik) atau (None, detik)."""
    t0 = time.time()
    body = json.dumps({'model': model, 'messages': [{'role': 'user', 'content': pesan}],
                       'max_tokens': max_tokens}).encode()
    req = urllib.request.Request(BASE + '/chat/completions', data=body,
                                 headers=HDR, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read().decode()
    except Exception as e:
        return None, round(time.time() - t0, 1), str(e)[:100]
    # parse SSE
    potongan, isi_penuh = [], None
    try:
        # format A: satu JSON di awal (9router beberapa backend begitu)
        d = json.loads(raw)
        isi_penuh = d['choices'][0]['message']['content']
    except Exception:
        isi_penuh = None
    if not isi_penuh:
        for baris in raw.splitlines():
            if baris.startswith('data:'):
                payload = baris[5:].strip()
                if payload == '[DONE]':
                    continue
                try:
                    d = json.loads(payload)
                    c = (d.get('choices') or [{}])[0]
                    delta = (c.get('delta') or {}).get('content') \
                        or (c.get('message') or {}).get('content') or ''
                    if delta:
                        potongan.append(delta)
                except Exception:
                    pass
        isi_penuh = ''.join(potongan)
    return (isi_penuh or '').strip(), round(time.time() - t0, 1), None


KALIMAT = ('Berdasarkan hasil penelitian yang telah dilaksanakan diatas, '
           'maka dapat ditarik kesimpulan bahwa data yang penulis kumpulkan '
           'adalah tidak signifikan secara statistic.')

PESAN = ('Perbaiki kalimat tesis berikut sesuai kaidah PUEBI (bahasa Indonesia baku). '
         'Balas HANYA kalimat yang sudah diperbaiki, tanpa penjelasan:\n\n' + KALIMAT)

KANDA = ('diatas', 'statistic', 'dilaksanakan')

model_uji = ['inferhub/ag/gemini-3.8-flash-high',
             'inferhub/ag/gemini-3.7-flash-high',
             'inferhub/ag/claude-sonnet-4-6',
             'inferhub/ali/glm-5.2',
             'inferhub/ali/qwen3.8-max',
             'inferhub/ali/deepseek-v4-flash-0731',
             'inferhub/cb/deepseek-v4.1-flash',
             'inferhub/ali/kimi-k3']

print(f'{"model":<38} {"t(s)":>6} {"perbaiki":>9} {"kata_baku":>10}')
print('-' * 70)
for mo in model_uji:
    jawab, dt, err = tanya(mo, PESAN)
    if err:
        print(f'{mo:<38} {dt:>6} ERROR: {err}')
        continue
    # skor: berapa kata tidak-baku yang hilang
    hilang = sum(1 for k in KANDA if k.lower() not in jawab.lower())
    ok_kalimat = len(jawab) > 30 and jawab[-1] in '.!?'
    print(f'{mo:<38} {dt:>6} {str(ok_kalimat):>9} {hilang}/3{"":>7}')
    print(f'  ↳ {jawab[:120]}')
