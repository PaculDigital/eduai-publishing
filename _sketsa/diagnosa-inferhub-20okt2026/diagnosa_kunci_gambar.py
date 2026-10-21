"""Diagnosa: KENAPA InferHub bilang "Credits exhausted" padahal saldo $7,57.

Hipotesis: kunci aplikasi BUKAN kunci InferHub yang punya saldo.
Uji: panggil /v1/images/generations dengan kunci yang BERBEDA, lihat
kode galatnya. 14018 = kredit habis (kunci benar, saldo kosong);
401/403 = kunci salah.
"""
import os
import sys

import requests

BASE = 'https://api.inferhub.dev/v1'
MODEL = 'cb/gemini-2.5-flash-image'

kunci_uji = {
    'aplikasi (sk-air...)': os.getenv('K1', ''),
    'inferhub langsung (sk-airo-iQ9o...)': os.getenv('K2', ''),
}


def coba(nama, key, model=MODEL):
    if not key:
        print(f'  {nama}: (kunci kosong — dilewati)')
        return None
    try:
        r = requests.post(
            f'{BASE}/images/generations',
            headers={'Content-Type': 'application/json',
                     'Authorization': f'Bearer {key}'},
            json={'model': model, 'prompt': 'a red apple on white background',
                  'n': 1, 'size': '1024x1024',
                  'response_format': 'b64_json'},
            timeout=120)
    except Exception as e:                                    # noqa: BLE001
        print(f'  {nama}: ERROR {type(e).__name__}: {str(e)[:90]}')
        return None
    txt = r.text[:220].replace('\n', ' ')
    print(f'  {nama}: HTTP {r.status_code} — {txt}')
    return r.status_code


print('=== UJI KUNCI GAMBAR ===')
for nama, k in kunci_uji.items():
    print(f'\n[{nama}]')
    coba(nama, k, MODEL)

print()
print('=== BACA SALDO per kunci ===')
for nama, k in kunci_uji.items():
    if not k:
        continue
    try:
        r = requests.get(f'{BASE}/dashboard/billing/credit_grants',
                         headers={'Authorization': f'Bearer {k}'}, timeout=40)
        print(f'  {nama}: HTTP {r.status_code} {r.text[:140]}')
    except Exception as e:                                    # noqa: BLE001
        print(f'  {nama}: ERROR {type(e).__name__}')

sys.exit(0)
