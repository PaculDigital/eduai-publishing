#!/usr/bin/env python3
"""Perkokoh keamanan oo.bikinaja.id dengan Cloudflare Access.

MASALAH: oo.bikinaja.id terbuka publik. Siapa pun bisa pakai server
OnlyOffice kita sebagai editor gratis.

SOLUSI 2 LAPIS:
  1. Cloudflare Access -> wajib login sebelum sampai ke OnlyOffice.
  2. Service Token    -> supaya EDITOR kita sendiri tetap bisa memuat
     aset (api.js, sdkjs) tanpa login manual dari browser client.

CARA KERJA SERVICE TOKEN:
  Cloudflare Access memblokir request TANPA cookie/token.
  Browser client (yang buka /edit/{id}) tidak punya token itu.
  Solusi: aplikasi kita jadi PROXY. Request dari browser ke
  /oo-aset/* diteruskan server kita ke oo.bikinaja.id dengan
  menyisipkan header Service Token.

  Jadi: browser tidak pernah langsung ke oo.bikinaja.id.

Jalankan: python3 scripts/perkokoh_oo.py
"""
import json
import os
import sys

import httpx

VAULT = '/opt/data/vault/cloudflare.json'
APP_DIR = '/opt/data/services/eduai-publishing'
ENV_FILE = f'{APP_DIR}/.env'

with open(VAULT) as f:
    v = json.load(f)
TOK = v['api_token']
ACC = v['account_id']
ZONE = v['zones']['bikinaja.id']
H = {'Authorization': f'Bearer {TOK}', 'Content-Type': 'application/json'}
API = 'https://api.cloudflare.com/client/v4'

DOMAIN = 'oo.bikinaja.id'


def api(method, path, body=None):
    url = f'{API}{path}'
    r = httpx.request(method, url, headers=H, json=body, timeout=40)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {'raw': r.text[:200]}


print('=' * 62)
print('LANGKAH 1 — Buat Service Token (kunci akses untuk aplikasi kita)')
print('=' * 62)
sd, sj = api('POST', f'/accounts/{ACC}/access/service_tokens',
             {'name': 'eduai-onlyoffice', 'duration': '8760h'})
if sd in (200, 201) and sj.get('success'):
    st = sj['result']
    ST_CLIENT = st['client_id']
    ST_SECRET = st['client_secret']
    print(f'  ✅ Service Token dibuat')
    print(f'     client_id: {ST_CLIENT}')
    print(f'     secret   : {"<tersimpan>" if ST_SECRET else "(tidak dikembalikan)"}')
else:
    print(f'  ⚠️ HTTP {sd}: {str(sj.get("errors"))[:250]}')
    # mungkin sudah ada
    sd2, sj2 = api('GET', f'/accounts/{ACC}/access/service_tokens')
    for t in (sj2.get('result') or []):
        if t.get('name') == 'eduai-onlyoffice':
            ST_CLIENT, ST_SECRET = t['client_id'], None
            print(f'  (pakai yang sudah ada: {ST_CLIENT})')
            break
    else:
        sys.exit('GAGAL buat service token')

print()
print('=' * 62)
print('LANGKAH 2 — Buat Access Application untuk oo.bikinaja.id')
print('=' * 62)
app_body = {
    'name': 'EduAi OnlyOffice (terlindungi)',
    'domain': DOMAIN,
    'type': 'self_hosted',
    'session_duration': '24h',
    'app_launcher_visible': False,
    'auto_redirect_to_identity': False,
    # policy: hanya service token yang boleh (tanpa login email)
    'allowed_idps': [],
}
ad, aj = api('POST', f'/accounts/{ACC}/access/apps', app_body)
if ad in (200, 201) and aj.get('success'):
    APP_ID = aj['result']['id']
    APP_AUD = aj['result']['aud']
    print(f'  ✅ App dibuat: id={APP_ID}  aud={APP_AUD}')
else:
    print(f'  HTTP {ad}: {str(aj.get("errors"))[:250]}')
    # cek yang sudah ada
    _, lj = api('GET', f'/accounts/{ACC}/access/apps')
    for a in (lj.get('result') or []):
        if a.get('domain') == DOMAIN:
            APP_ID, APP_AUD = a['id'], a['aud']
            print(f'  (pakai yang ada: {APP_ID})')
            break
    else:
        sys.exit('GAGAL buat Access app')

print()
print('=' * 62)
print('LANGKAH 3 — Policy: izinkan SERVICE TOKEN + Bos (email)')
print('=' * 62)

# 3a. policy untuk service token (bypass mesin-ke-mesin)
pol_body = {
    'name': 'Izinkan Service Token EduAi',
    'decision': 'non_identity',
    'include': [{'service_token': {'token_id': ST_CLIENT}}],
}
pd, pj = api('POST', f'/accounts/{ACC}/access/apps/{APP_ID}/policies', pol_body)
print(f'  service-token policy: HTTP {pd} sukses={pj.get("success")}')

# 3b. policy untuk Bos (login email OTP) - opsional
pol2 = {
    'name': 'Izinkan Bos (email OTP)',
    'decision': 'allow',
    'include': [{'email_domain': {'domain': 'bikinaja.id'}}],
}
p2d, p2j = api('POST', f'/accounts/{ACC}/access/apps/{APP_ID}/policies', pol2)
print(f'  email policy        : HTTP {p2d} sukses={p2j.get("success")}')

print()
print('=' * 62)
print('LANGKAH 4 — Simpan kredensial ke .env (tidak ditampilkan)')
print('=' * 62)
lines = []
if os.path.exists(ENV_FILE):
    with open(ENV_FILE) as f:
        lines = [l for l in f.read().splitlines()
                 if not l.startswith(('EDUAI_CF_ACCESS_', 'EDUAI_OO_VAULT'))]
baru = [
    f'EDUAI_OO_AUD={APP_AUD}',
    f'EDUAI_CF_ACCESS_CLIENT_ID={ST_CLIENT}',
]
if ST_SECRET:
    baru.append(f'EDUAI_CF_ACCESS_CLIENT_SECRET={ST_SECRET}')
lines += baru
with open(ENV_FILE, 'w') as f:
    f.write('\n'.join(lines) + '\n')
os.chmod(ENV_FILE, 0o600)
print(f'  ✅ {len(baru)} variabel ditulis ke .env (chmod 600)')
for b in baru:
    print('     ', b.split('=')[0] + '=<tersimpan>')

print()
print('=' * 62)
print('SELESAI. Ringkasan:')
print('=' * 62)
print(f'  App ID      : {APP_ID}')
print(f'  AUD         : {APP_AUD}')
print(f'  Service ID  : {ST_CLIENT}')
print(f'  Domain      : {DOMAIN}')
