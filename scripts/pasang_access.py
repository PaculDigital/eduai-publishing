#!/usr/bin/env python3
"""Pasang Cloudflare Access di oo.bikinaja.id — "hidup tapi tidak bisa diakses".

PERMINTAAN BOS:
  Subdomain oo.bikinaja.id HARUS ADA (editor OnlyOffice butuh akses
  langsung ke sana — cara RESMI, bukan proxy tambalan), TAPI kalau
  ditembak langsung dari publik -> DITOLAK.

CARA KERJA:
  1. Hidupkan DNS + aturan tunnel untuk oo.bikinaja.id
  2. Buat Service Token (client_id + client_secret) = "kunci" untuk editor
  3. Buat Access Application (self_hosted) di domain itu
  4. Policy: HANYA service token yang boleh lewat (decision: non_identity)
     -> Manusia yang buka oo.bikinaja.id akan DITOLAK/diminta login
     -> Editor kita bawa header CF-Access-Client-Id/Secret -> LOLOS

Idempotent: aman dijalankan berulang.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import httpx

BASE = Path(__file__).resolve().parent.parent
VAULT = '/opt/data/vault/cloudflare.json'
CF = 'https://api.cloudflare.com/client/v4'
DOMAIN = 'oo.bikinaja.id'
ZONE = 'bikinaja.id'
NAMA_TOKEN = 'eduai-onlyoffice'

d = json.load(open(VAULT))
TOK, ACC, ZID = d['api_token'], d['account_id'], d['zones']['bikinaja.id']
H = {'Authorization': f'Bearer {TOK}', 'Content-Type': 'application/json'}

HIJAU, MERAH, BIRU, TEBAL, N = ('\033[0;32m', '\033[0;31m',
                                '\033[0;34m', '\033[1m', '\033[0m')


def ok(m): print(f'  {HIJAU}✓{N} {m}')
def er(m): print(f'  {MERAH}✗{N} {m}')
def inf(m): print(f'  {BIRU}→{N} {m}')
def jd(m): print(f'\n{TEBAL}{BIRU}═══ {m} ═══{N}')


def cari_tunnel() -> str:
    r = httpx.get(f'{CF}/accounts/{ACC}/cfd_tunnel', headers=H, timeout=30)
    for t in (r.json().get('result') or []):
        if 'bikinaja' in (t.get('name') or '').lower():
            return t['id']
    r2 = httpx.get(f'{CF}/accounts/{ACC}/cfd_tunnel', headers=H,
                   params={'is_deleted': 'false'}, timeout=30)
    hasil = r2.json().get('result') or []
    if hasil:
        return hasil[0]['id']
    er('tunnel tidak ditemukan')
    sys.exit(1)


print('=' * 70)
print('  PASANG CLOUDFLARE ACCESS — oo.bikinaja.id')
print('  "Hidup tapi tidak bisa ditembak langsung dari publik"')
print('=' * 70)

# ════════════════════════════════════════════════════════════════════
jd('1. Hidupkan DNS + aturan tunnel')
# ════════════════════════════════════════════════════════════════════
TUNNEL = cari_tunnel()
inf(f'tunnel: {TUNNEL}')

ip_oo = subprocess.run(
    ['docker', 'inspect', '-f',
     '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', 'oo-converter'],
    capture_output=True, text=True).stdout.strip() or '172.17.0.7'
inf(f'IP oo-converter: {ip_oo}')

# DNS
r = httpx.get(f'{CF}/zones/{ZID}/dns_records', headers=H,
              params={'name': DOMAIN}, timeout=25)
recs = r.json().get('result') or []
payload = {'type': 'CNAME', 'name': DOMAIN,
           'content': f'{TUNNEL}.cfargotunnel.com',
           'proxied': True, 'ttl': 1,
           'comment': 'EduAi OnlyOffice (Cloudflare Access)'}
if recs:
    rid = recs[0]['id']
    rr = httpx.put(f'{CF}/zones/{ZID}/dns_records/{rid}', headers=H,
                   json=payload, timeout=30)
    ok(f'DNS diperbarui (proxied)') if rr.json().get('success') else er('DNS gagal')
else:
    rr = httpx.post(f'{CF}/zones/{ZID}/dns_records', headers=H,
                    json=payload, timeout=30)
    ok('DNS CNAME dibuat (proxied)') if rr.json().get('success') else er('DNS gagal')

# Aturan tunnel
cfg_url = f'{CF}/accounts/{ACC}/cfd_tunnel/{TUNNEL}/configurations'
cfg = httpx.get(cfg_url, headers=H, timeout=30).json().get('result', {}).get('config', {}) or {}
ingress = cfg.get('ingress') or []
ingress = [x for x in ingress if x.get('hostname') != DOMAIN]
catch = [x for x in ingress if 'hostname' not in x]
lain = [x for x in ingress if 'hostname' in x]
baru = ([{'hostname': DOMAIN, 'service': f'http://{ip_oo}:80'}]
        + lain + (catch or [{'service': 'http_status:404'}]))
rr = httpx.put(cfg_url, headers=H,
               json={'config': {**cfg, 'ingress': baru}}, timeout=30)
ok(f'aturan tunnel: {DOMAIN} -> {ip_oo}:80') if rr.json().get('success') \
    else er(f'tunnel gagal: {rr.text[:200]}')

# ════════════════════════════════════════════════════════════════════
jd('2. Buat Service Token (kunci khusus editor)')
# ════════════════════════════════════════════════════════════════════
r = httpx.get(f'{CF}/accounts/{ACC}/access/service_tokens', headers=H, timeout=25)
lama = [t for t in (r.json().get('result') or []) if t.get('name') == NAMA_TOKEN]
if lama:
    inf(f'token lama ditemukan ({lama[0]["client_id"][:14]}...) — dihapus')
    httpx.delete(f'{CF}/accounts/{ACC}/access/service_tokens/{lama[0]["id"]}',
                 headers=H, timeout=25)
    ok('token lama dihapus (secret lama tidak bisa diambil)')

# SIMPAN dulu token lama kalau ada (biar tidak hilang kalau gagal)
env = BASE / '.env'
env_lama = env.read_text() if env.exists() else ''

r = httpx.post(f'{CF}/accounts/{ACC}/access/service_tokens', headers=H,
               json={'name': NAMA_TOKEN, 'duration': '8760h'}, timeout=30)
j = r.json()
if not j.get('success'):
    er(f'gagal: {[(e.get("code"), e.get("message")) for e in (j.get("errors") or [])]}')
    sys.exit(1)

CID = j['result']['client_id']
CSEC = j['result']['client_secret']
TID = j['result']['id']
ok(f'token dibuat (client_id: {CID[:14]}...)')

s = env_lama
for k, v in [('EDUAI_OO_CF_ACCESS_ID', CID), ('EDUAI_OO_CF_ACCESS_SECRET', CSEC)]:
    s = re.sub(rf'^{k}=.*$', f'{k}={v}', s, flags=re.M) if re.search(rf'^{k}=', s, re.M) \
        else s + f'\n{k}={v}\n'
env.write_text(s)
env.chmod(0o600)
ok('.env diperbarui (client_id + secret) — file 600')

# ════════════════════════════════════════════════════════════════════
jd('3. Buat Access Application')
# ════════════════════════════════════════════════════════════════════
r = httpx.get(f'{CF}/accounts/{ACC}/access/apps', headers=H, timeout=25)
apps = [a for a in (r.json().get('result') or []) if a.get('domain') == DOMAIN]
if apps:
    APP_ID = apps[0]['id']
    inf(f'app sudah ada (id: {APP_ID[:8]}...)')
    httpx.put(f'{CF}/accounts/{ACC}/access/apps/{APP_ID}', headers=H,
              json={'name': 'EduAi OnlyOffice', 'domain': DOMAIN,
                    'type': 'self_hosted', 'session_duration': '24h'},
              timeout=30)
    ok('app diperbarui')
else:
    rr = httpx.post(f'{CF}/accounts/{ACC}/access/apps', headers=H, json={
        'name': 'EduAi OnlyOffice', 'domain': DOMAIN, 'type': 'self_hosted',
        'session_duration': '24h', 'app_launcher_visible': False,
    }, timeout=30)
    jj = rr.json()
    if not jj.get('success'):
        er(f'gagal: {[(e.get("code"), e.get("message")) for e in (jj.get("errors") or [])]}')
        sys.exit(1)
    APP_ID = jj['result']['id']
    ok(f'app dibuat (id: {APP_ID[:8]}...)')

# ════════════════════════════════════════════════════════════════════
jd('4. Policy: HANYA service token boleh lewat')
# ════════════════════════════════════════════════════════════════════
r = httpx.get(f'{CF}/accounts/{ACC}/access/apps/{APP_ID}/policies',
              headers=H, timeout=25)
pol = r.json().get('result') or []
for p in pol:
    httpx.delete(f'{CF}/accounts/{ACC}/access/apps/{APP_ID}/policies/{p["id"]}',
                 headers=H, timeout=25)
if pol:
    inf(f'{len(pol)} policy lama dihapus (biar bersih)')

body = {
    'name': 'Service Token Only',
    'decision': 'non_identity',      # tidak perlu login manusia
    'precedence': 1,
    'include': [{'service_token': {'token_id': TID}}],
}
rr = httpx.post(f'{CF}/accounts/{ACC}/access/apps/{APP_ID}/policies',
                headers=H, json=body, timeout=30)
jj = rr.json()
if jj.get('success'):
    ok('policy: non_identity (service token saja) — manusia DITOLAK')
else:
    er(f'gagal: {[(e.get("code"), e.get("message")) for e in (jj.get("errors") or [])]}')

# ════════════════════════════════════════════════════════════════════
jd('5. Simpan konfigurasi')
# ════════════════════════════════════════════════════════════════════
arsip = sorted((BASE / '_arsip').glob('security-*'))
if arsip:
    f = arsip[-1] / 'cloudflare_access.json'
    f.write_text(json.dumps({
        'app_id': APP_ID, 'domain': DOMAIN, 'tunnel': TUNNEL,
        'service_token_id': TID, 'service_token_client_id': CID,
        'policy': 'non_identity / service_token only',
        'catatan': 'secret service token ada di .env (EDUAI_OO_CF_ACCESS_SECRET)',
    }, indent=2))
    ok(f'disimpan: {f}')

print()
print('=' * 70)
print(f'  {TEBAL}{HIJAU}SELESAI{N}')
print('=' * 70)
print(f'''
  Subdomain     : https://{DOMAIN}
  Access App    : {APP_ID}
  Service Token : {CID[:14]}...

  Sekarang subdomain HIDUP tapi manusia TIDAK BISA masuk.
  Editor kita masuk pakai service token (header CF-Access-*).

  LANJUTKAN: jalankan scripts/uji_access.py untuk membuktikan.
''')
