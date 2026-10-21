"""Saring daftar model InferHub: hanya yang bisa GAMBAR (output image)."""
import json
import os
import sys

import httpx

K = os.getenv('K') or ''
BASE = 'https://api.inferhub.dev/v1'
H = {'Authorization': f'Bearer {K}'}

r = httpx.get(f'{BASE}/models', headers=H, timeout=60)
items = r.json().get('data') or []
print('total model:', len(items))
print()

KUNCI_GAMBAR = ('image', 'flux', 'diffusion', 'sdxl', 'dall-e', 'dalle',
                'imagen', 'nano-banana', 'picture', 'draw', 'pix',
                'stable-diffusion', 'kolors', 'seedream', 'recraft')

gambar = []
for it in items:
    mid = str(it.get('id') or '')
    if not mid.strip('/'):
        continue
    blob = json.dumps(it).lower()
    if any(k in mid.lower() for k in KUNCI_GAMBAR):
        out = it.get('output_modalities') or it.get('output') or ''
        gambar.append((mid, str(out)[:40]))

print('=== MODEL YANG NAMANYA MENYIRATKAN GAMBAR ===')
for m, o in sorted(set(gambar)):
    print(f'  {m:45s} out={o}')

print()
print('jumlah kandidat:', len(set(gambar)))
sys.exit(0)
