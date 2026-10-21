#!/usr/bin/env python3
"""HAPUS rute publik oo.bikinaja.id + buat /oo/asset (auth kita).

MASALAH: oo.bikinaja.id terbuka publik -> server kita bisa dipakai
sebagai editor gratis oleh siapa pun.

SOLUSI (tanpa butuh izin Zero Trust Cloudflare):
  1. HAPUS ingress 'oo.bikinaja.id' dari tunnel -> domain itu MATI total.
  2. HAPUS record DNS oo.bikinaja.id -> tidak resolve sama sekali.
  3. Editor tetap hidup: browser memuat aset lewat
     https://eduai.bikinaja.id/oo/asset/...  (auth kita yang jaga).

Alur baru:
  Browser (sudah login) -> eduai.bikinaja.id/oo/asset/api.js
                        -> app kita teruskan ke 172.17.0.7 (internal)
  Browser            -> iframe /oo/asset/.../documenteditor/index.html
  OnlyOffice         -> http://172.17.0.9:8000/oo/unduh/<token>  (internal)

  oo.bikinaja.id = MATI. Tidak ada jalan masuk dari luar.
"""
import json
import sys

import httpx

VAULT = '/opt/data/vault/cloudflare.json'
with open(VAULT) as f:
    v = json.load(f)
TOK = v['api_token']
ACC = v['account_id']
ZONE = v['zones']['bikinaja.id']
H = {'Authorization': f'Bearer {TOK}', 'Content-Type': 'application/json'}
API = 'https://api.cloudflare.com/client/v4'
TID = '8ae633d2-4726-47e1-aa5d-1d90fe13ffb1'
DOMAIN = 'oo.bikinaja.id'


def api(method, path, body=None):
    r = httpx.request(method, f'{API}{path}', headers=H, json=body, timeout=40)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {'raw': r.text[:200]}


print('=' * 62)
print('LANGKAH 1 — Hapus ingress oo.bikinaja.id dari tunnel')
print('=' * 62)
sd, sj = api('GET', f'/accounts/{ACC}/cfd_tunnel/{TID}/configurations')
cfg = (sj.get('result') or {}).get('config') or {}
ing = cfg.get('ingress') or []
print(f'  sebelum: {len(ing)} ingress')

sisa = [i for i in ing if i.get('hostname') != DOMAIN]
hilang = len(ing) - len(sisa)

if hilang:
    cfg['ingress'] = sisa
    ud, uj = api('PUT', f'/accounts/{ACC}/cfd_tunnel/{TID}/configurations',
                 {'config': cfg})
    if uj.get('success'):
        print(f'  ✅ ingress {DOMAIN} DIHAPUS -> sisa {len(sisa)}')
    else:
        print(f'  ❌ gagal: {str(uj.get("errors"))[:200]}')
        sys.exit(1)
else:
    print(f'  (sudah tidak ada di ingress)')

print()
print('=' * 62)
print('LANGKAH 2 — Hapus record DNS oo.bikinaja.id')
print('=' * 62)
rd, rj = api('GET', f'/zones/{ZONE}/dns_records', None) if False else (None, None)
r = httpx.get(f'{API}/zones/{ZONE}/dns_records',
              headers={'Authorization': f'Bearer {TOK}'},
              params={'name': DOMAIN}, timeout=30)
recs = (r.json().get('result') or [])
for rec in recs:
    dd, dj = api('DELETE', f'/zones/{ZONE}/dns_records/{rec["id"]}')
    print(f'  {rec["type"]} {rec["name"]} -> '
          f'{"✅ dihapus" if dj.get("success") else "❌ gagal"}')
if not recs:
    print('  (tidak ada record DNS)')

print()
print('=' * 62)
print('LANGKAH 3 — Verifikasi')
print('=' * 62)
for d in [DOMAIN, 'eduai.bikinaja.id']:
    try:
        rr = httpx.get(f'https://{d}/', timeout=15, follow_redirects=True)
        print(f'  https://{d}/  -> HTTP {rr.status_code}')
    except Exception as e:
        print(f'  https://{d}/  -> TIDAK BISA DIAKSES ({str(e)[:60]})')

print()
print('=' * 62)
print('SELESAI. oo.bikinaja.id sudah DITUTUP.')
print('=' * 62)
