"""Cari model gambar InferHub ASLI yang masih hidup (bukan cb/* CodeBuddy)."""
import os
import sys

import httpx

K = os.getenv('K') or ''
BASE = 'https://api.inferhub.dev/v1'
H = {'Content-Type': 'application/json', 'Authorization': f'Bearer {K}'}

kandidat = [
    'infer/flux-schnell',
    'infer/flux-dev',
    'infer/sdxl',
    'black-forest-labs/flux-schnell',
    'google/gemini-2.5-flash-image',
    'openai/gpt-image-1',
    'stabilityai/stable-diffusion-xl',
    'qwen/qwen-image',
]

print('=== COBA MODEL GAMBAR (bukan cb/*) ===')
hidup = []
for m in kandidat:
    try:
        r = httpx.post(f'{BASE}/images/generations', headers=H, timeout=120,
                       json={'model': m, 'prompt': 'a red apple, white background',
                             'n': 1, 'size': '1024x1024',
                             'response_format': 'b64_json'})
        txt = r.text[:150].replace('\n', ' ')
        waktu = 'HIDUP' if r.status_code == 200 else f'{r.status_code}'
        print(f'  [{waktu:6s}] {m}')
        if r.status_code == 200:
            d = r.json()
            adakah = bool(d.get('data') and d['data'][0].get('b64_json'))
            print(f'             -> b64 ada? {adakah}')
            if adakah:
                hidup.append(m)
        else:
            print(f'             {txt}')
    except Exception as e:                                    # noqa: BLE001
        print(f'  [ERR   ] {m} — {type(e).__name__}: {str(e)[:70]}')

print()
print('MODEL HIDUP:', hidup or 'TIDAK ADA SATU PUN')
sys.exit(0 if hidup else 1)
