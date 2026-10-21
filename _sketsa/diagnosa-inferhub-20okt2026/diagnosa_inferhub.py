"""Diagnosa InferHub: apakah 14018 = kredit habis untuk MODEL GAMBAR saja?"""
import os
import sys

import httpx

K = os.getenv('K') or ''
BASE = 'https://api.inferhub.dev/v1'
H = {'Content-Type': 'application/json', 'Authorization': f'Bearer {K}'}

print('=== 1. SALDO AKUN (lewat MCP dashboard) ===')
try:
    r = httpx.get(f'{BASE}/credits', headers=H, timeout=40)
    print(f'  /credits HTTP {r.status_code}: {r.text[:200]}')
except Exception as e:                                        # noqa: BLE001
    print(f'  /credits ERROR {type(e).__name__}: {str(e)[:80]}')

print()
print('=== 2. GAMBAR: model yang dipakai aplikasi ===')
try:
    r = httpx.post(f'{BASE}/images/generations', headers=H, timeout=150,
                   json={'model': 'cb/gemini-2.5-flash-image',
                         'prompt': 'a red apple on white background',
                         'n': 1, 'size': '1024x1024',
                         'response_format': 'b64_json'})
    print(f'  HTTP {r.status_code}: {r.text[:300]}')
except Exception as e:                                        # noqa: BLE001
    print(f'  ERROR {type(e).__name__}: {str(e)[:100]}')

print()
print('=== 3. TEKS: apakah kunci masih hidup? ===')
try:
    r = httpx.post(f'{BASE}/chat/completions', headers=H, timeout=90,
                   json={'model': 'cb/gemini-2.5-flash',
                         'messages': [{'role': 'user', 'content': 'hi'}],
                         'max_tokens': 5})
    print(f'  HTTP {r.status_code}: {r.text[:250]}')
except Exception as e:                                        # noqa: BLE001
    print(f'  ERROR {type(e).__name__}: {str(e)[:100]}')

sys.exit(0)
