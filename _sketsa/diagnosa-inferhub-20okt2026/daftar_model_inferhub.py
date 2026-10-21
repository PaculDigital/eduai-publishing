"""Baca DAFTAR MODEL ASLI dari InferHub, saring yang bisa gambar."""
import json
import os
import sys

import httpx

K = os.getenv('K') or ''
BASE = 'https://api.inferhub.dev/v1'
H = {'Authorization': f'Bearer {K}'}

r = httpx.get(f'{BASE}/models', headers=H, timeout=60)
print('HTTP', r.status_code)
if r.status_code != 200:
    print(r.text[:300])
    sys.exit(1)

data = r.json()
items = data.get('data') or data.get('models') or []
print('jumlah model:', len(items))

#  Saring: nama / modality yang menyiratkan GAMBAR
kata = ('image', 'flux', 'diffusion', 'sdxl', 'dall', 'imagen', 'banana',
        'pix', 'draw', 'picture', 'vision-gen')
gambar = []
for it in items:
    mid = str(it.get('id') or it.get('name') or '')
    neg = json.dumps(it).lower()
    if any(k in mid.lower() for k in kata) or 'image' in neg:
        gambar.append(mid)

print()
print('=== MODEL BERPOTENSI GAMBAR ===')
for m in sorted(set(gambar)):
    print(' ', m)

print()
print('=== SEMUA MODEL (30 pertama) ===')
for it in items[:30]:
    print(' ', it.get('id') or it.get('name'))
sys.exit(0)
