#!/usr/bin/env python3
"""PROBE 9router v7 (FIX) — bandingkan model inferhub utk revisi teks akademik.

Perbaikan dari v5:
  - Parser: baris pertama JSON TELANJANG + baris 'data: {...}' + 'data: [DONE]'
  - max_tokens 2000 (model reasoning memakan token utk berpikir dulu)
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


def tanya(model, pesan, max_tokens=2000, timeout=240):
    """Kirim chat → (teks_jawaban, detik, error).

    Parser menangani 3 bentuk baris:
      1. JSON telanjang di baris pertama  → message.content / reasoning_content
      2. 'data: {...' (SSE standar)        → delta.content
      3. 'data: [DONE]'
    """
    t0 = time.time()
    body = json.dumps({'model': model, 'messages': [{'role': 'user', 'content': pesan}],
                       'max_tokens': max_tokens}).encode()
    req = urllib.request.Request(BASE + '/chat/completions', data=body,
                                 headers=HDR, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
    except Exception as e:
        return None, round(time.time() - t0, 1), f'{type(e).__name__}: {str(e)[:120]}'

    isi, n_reason = [], 0
    for baris in raw.splitlines():
        baris = baris.strip()
        if not baris or baris == 'data: [DONE]':
            continue
        if baris.startswith('data:'):
            baris = baris[5:].strip()
        if baris == '[DONE]':
            continue
        try:
            d = json.loads(baris)
        except Exception:
            continue
        c = (d.get('choices') or [{}])[0]
        msg = c.get('message') or {}
        if msg.get('reasoning_content'):
            n_reason += len(msg['reasoning_content'])
        if msg.get('content'):
            isi.append(msg['content'])
        if (c.get('delta') or {}).get('content'):
            isi.append(c['delta']['content'])
    return (''.join(isi)).strip(), round(time.time() - t0, 1), \
        (f'reasoning {n_reason} char, content kosong' if not isi and n_reason else None)


KALIMAT = ('Berdasarkan hasil penelitian yang telah dilaksanakan diatas, '
           'maka dapat ditarik kesimpulan bahwa data yang penulis kumpulkan '
           'adalah tidak signifikan secara statistic.')
PESAN = ('Perbaiki kalimat tesis berikut sesuai kaidah PUEBI (bahasa Indonesia baku). '
         'Balas HANYA kalimat yang sudah diperbaiki, tanpa penjelasan:\n\n' + KALIMAT)
KANDA = ('diatas', 'statistic', 'dilaksanakan')

model_uji = ['inferhub/cb/deepseek-v4.1-flash',
             'inferhub/ali/qwen3.8-max',
             'inferhub/ag/gemini-3.8-flash-high',
             'inferhub/ali/glm-5.2',
             'inferhub/ag/claude-sonnet-4-6',
             'inferhub/ali/kimi-k3']

print(f'{"model":<38} {"t(s)":>6} {"baku":>5} {"kalimat":>8}')
print('-' * 66)
hasil_ok = []
for mo in model_uji:
    jawab, dt, err = tanya(mo, PESAN)
    if err:
        print(f'{mo:<38} {dt:>6}   ERR: {err}')
        continue
    hilang = sum(1 for k in KANDA if k.lower() not in jawab.lower())
    ok_kal = len(jawab) > 30 and jawab[-1] in '.!?'
    print(f'{mo:<38} {dt:>6} {hilang}/3 {str(ok_kal):>8}   {jawab[:90]}')
    if ok_kal and hilang >= 2:
        hasil_ok.append(mo)

print()
print('LAYAK (baku>=2 + kalimat utuh):', hasil_ok if hasil_ok else 'TIDAK ADA')
