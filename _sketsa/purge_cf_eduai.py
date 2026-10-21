"""Purge cache Cloudflare zona bikinaja.id — akar editor nyangkut.

BUKTI (12Okt26): api.js lewat CF = hash LAMA (fc076386), OO asli = 884b8d73,
cf-cache-status HIT, age 35377 dtk (9,8 jam). Ini persis yang dikatakan
skill cloudflare-api: rule cache pakai override_origin TTL 1 tahun
=> purge WAJIB tiap deploy/rebranding.

Jalankan: purge SEMUA (paling pasti) lalu verifikasi hash api.js.
"""
import json
import urllib.request
import urllib.error

TOK = json.load(open('/opt/data/vault/cloudflare.json'))['api_token']
ZONE = 'da1822e6237bdf1bc34129e2b4ee5ef7'   # bikinaja.id
BASE = 'https://api.cloudflare.com/client/v4'


def api(m, p, b=None):
    d = json.dumps(b).encode() if b else None
    req = urllib.request.Request(
        BASE + p, data=d, method=m,
        headers={'Authorization': f'Bearer {TOK}',
                 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return True, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return False, json.loads(e.read().decode())
    except Exception as e:
        return False, {'err': str(e)[:120]}


print('=== 1. purge SEMUA cache zona bikinaja.id ===')
ok, r = api('POST', f'/zones/{ZONE}/purge_cache', {'purge_everything': True})
print('  ok:', ok, '|', json.dumps(r.get('result', r))[:120])

print()
print('=== 2. daftar cache rule yang ada ===')
ok, rs = api('GET', f'/zones/{ZONE}/rulesets')
if ok:
    for s in rs.get('result', []):
        print('  %-46s phase=%s' % (s.get('name'), s.get('phase')))
