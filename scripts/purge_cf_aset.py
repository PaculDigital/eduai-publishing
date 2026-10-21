#!/usr/bin/env python3
"""Purge cache Cloudflare untuk aset editor (agar About.js baru terkirim).

Butuh: zone id + API token dari vault.
"""
import json
import subprocess
import sys
from pathlib import Path

VAULT = Path('/opt/data/vault/cloudflare.json')
ZONE_PAKU = 'da1822e6237bdf1bc34129e2b4ee5ef7'


def baca_kred():
    kandidat = [VAULT, Path('/opt/data/.cloudflare.json'),
                Path.home() / '.cloudflare.json']
    for p in kandidat:
        if p.exists():
            d = json.loads(p.read_text())
            tok = (d.get('api_token') or d.get('token')
                   or d.get('cloudflare_api_token'))
            zone = (d.get('zone_id') or d.get('zone')
                    or d.get('zona') or d.get('zoneId'))
            if tok:
                return tok, (zone or ZONE_PAKU)
            if tok and zone:
                print(f"[vault] {p} — token & zone OK")
                return tok, zone
            print(f"[vault] {p} — kunci: {list(d.keys())}")
    return None, None


TOKEN, ZONE = baca_kred()
if not TOKEN or not ZONE:
    print("❌ kredensial CF tidak lengkap")
    sys.exit(1)

print(f"zone: {ZONE[:8]}...")

# Purge SEMUA berkas (paling aman & pasti untuk 1x perubahan)
payload = json.dumps({'purge_everything': True})
cmd = [
    'curl', '-s', '-X', 'POST',
    f'https://api.cloudflare.com/client/v4/zones/{ZONE}/purge_cache',
    '-H', f'Authorization: Bearer {TOKEN}',
    '-H', 'Content-Type: application/json',
    '--data', payload,
]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
try:
    hasil = json.loads(r.stdout)
    print(f"\nsuccess : {hasil.get('success')}")
    if hasil.get('errors'):
        print(f"errors  : {hasil['errors']}")
    if hasil.get('result'):
        print(f"result  : {hasil['result']}")
    sys.exit(0 if hasil.get('success') else 1)
except Exception:
    print(f"respons mentah: {r.stdout[:500]}\n{r.stderr[:200]}")
    sys.exit(1)
