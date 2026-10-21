"""Uji model gambar InferHub ASLI (nama tanpa prefix cb/) — cari yang hidup."""
import os
import sys

import httpx

K = os.getenv('K') or ''
BASE = 'https://api.inferhub.dev/v1'
H = {'Content-Type': 'application/json', 'Authorization': f'Bearer {K}'}

#  Urut dari yang paling mungkin murah & cepat untuk ilustrasi buku.
kandidat = [
    'gemini-2.5-flash-image',
    'gemini-3.1-flash-image',
    'gpt-image-1.5',
    'gpt-image-2',
    'flux-schnell',
    'flux-dev',
    'nano-banana-2-lite',
    'seedream-4.0',
    'recraft-v4',
]

hidup = []
for m in kandidat:
    try:
        r = httpx.post(f'{BASE}/images/generations', headers=H, timeout=150,
                       json={'model': m,
                             'prompt': 'flat vector illustration of a child '
                                       'watching a stick shadow, white background',
                             'n': 1, 'size': '1024x1024',
                             'response_format': 'b64_json'})
        if r.status_code == 200:
            d = r.json()
            b64 = bool(d.get('data') and d['data'][0].get('b64_json'))
            kb = round(len(d['data'][0]['b64_json']) * 3 / 4 / 1024) if b64 else 0
            print(f'  [HIDUP] {m:32s} b64={b64} ~{kb} KB')
            if b64:
                hidup.append(m)
        else:
            pesan = r.text[:110].replace('\n', ' ')
            print(f'  [{r.status_code:5d}] {m:32s} {pesan}')
    except Exception as e:                                    # noqa: BLE001
        print(f'  [ERR  ] {m:32s} {type(e).__name__}: {str(e)[:60]}')

print()
print('MODEL GAMBAR HIDUP:', hidup or 'TIDAK ADA')
sys.exit(0 if hidup else 1)
