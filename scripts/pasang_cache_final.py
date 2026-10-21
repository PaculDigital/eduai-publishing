#!/usr/bin/env python3
"""PASANG Cache Rule CF — FINAL & TERVERIFIKASI.

Ekspresi ini SUDAH diuji diterima CF (lihat scripts/lihat_error_cf.py).
Plan Bos: contains()/matches() tidak ada; starts_with + not + and + or OK.

Sasaran cache (aset mesin OnlyOffice, isi identik untuk semua user):
  /oo/aset/web-apps/...          <- api.js (pemicu editor)
  /oo/aset/9.4.0-<hash>/...      <- sdkjs, web-apps, fonts, plugins

DIBLOKIR KERAS:
  /oo/aset/cache/...             <- NASKAH MAHASISWA
  (doc/ socket.io tidak masuk karena bukan di bawah 9.4.0- .../web-apps)

Bukti 481 request nyata: 450 aset mesin, 8 dokumen mahasiswa.
"""
import json
import urllib.error
import urllib.request

TOK = json.load(open('/opt/data/vault/cloudflare.json'))['api_token']
ZONE = 'da1822e6237bdf1bc34129e2b4ee5ef7'
BASE = 'https://api.cloudflare.com/client/v4'
NAMA = 'eduai-aset-editor-cache'
BAWAAN = ('Cloudflare Normalization Ruleset',
          'Cloudflare Managed Free Ruleset', 'DDoS L7 ruleset')


def api(m, p, b=None):
    d = json.dumps(b).encode() if b else None
    r = urllib.request.Request(f'{BASE}{p}', data=d, method=m,
                               headers={'Authorization': f'Bearer {TOK}',
                                        'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(r, timeout=30) as res:
            return True, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return False, json.loads(e.read().decode())
        except Exception:
            return False, {'err': f'HTTP {e.code}'}
    except Exception as e:
        return False, {'err': str(e)[:100]}


def bersihkan():
    ok, r = api('GET', f'/zones/{ZONE}/rulesets')
    if not ok:
        return ['cek-gagal']
    for x in r['result']:
        if x.get('name') not in BAWAAN:
            api('DELETE', f"/zones/{ZONE}/rulesets/{x['id']}")
    ok, r = api('GET', f'/zones/{ZONE}/rulesets')
    if ok:
        return [x['name'] for x in r['result'] if x.get('name') not in BAWAAN]
    return ['cek-gagal']


# EKSPRESI TERVERIFIKASI DITERIMA CF
EKSPRESI = (
    'starts_with(http.request.uri.path, "/oo/aset/") '
    'and ('
    'starts_with(http.request.uri.path, "/oo/aset/web-apps/") '
    'or starts_with(http.request.uri.path, "/oo/aset/9.4.0-")'
    ') '
    'and not starts_with(http.request.uri.path, "/oo/aset/cache/")'
)

RULE = {
    "expression": EKSPRESI,
    "action": "set_cache_settings",
    "action_parameters": {
        "cache": True,
        "edge_ttl": {"mode": "override_origin", "default": 31536000},
        "browser_ttl": {"mode": "override_origin", "default": 86400},
    },
    "description": "Aset mesin editor OnlyOffice - bukan dokumen mahasiswa",
}

print("=" * 74)
print("PASANG CACHE RULE CF (Opsi B) — FINAL")
print("=" * 74)

print("\n1. Bersihkan sisa…")
print("   sisa:", bersihkan() or 'tidak ada')

print("\n2. Ekspresi (terverifikasi diterima CF):")
for b in EKSPRESI.replace(' and ', '\n  and ').replace(' or ', '\n  or ').split('\n'):
    print("   " + b)

print("\n3. Pasang…")
ok, r = api('POST', f'/zones/{ZONE}/rulesets', {
    "name": NAMA, "kind": "zone",
    "phase": "http_request_cache_settings",
    "rules": [RULE],
})
if ok:
    print("   ✅ BERHASIL")
    print(f"   id    : {r['result']['id']}")
    print(f"   nama  : {r['result']['name']}")
else:
    print(f"   ❌ GAGAL: {json.dumps(r)[:400]}")

print("\n4. Ruleset akhir:")
ok, r = api('GET', f'/zones/{ZONE}/rulesets')
if ok:
    for x in r['result']:
        tanda = '   ⬅️ MILIK KITA' if x.get('name') == NAMA else ''
        print(f"   {x.get('phase'):36s} | {x.get('name')}{tanda}")
print("=" * 74)
