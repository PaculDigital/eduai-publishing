#!/usr/bin/env python3
"""Pasang DNS + aturan tunnel untuk EduAi Publishing.

Rute:
  eduai.bikinaja.id     -> http://<ip eduai-app>:8000   (portal)
  oo.bikinaja.id        -> http://<ip oo-converter>:80  (OnlyOffice Document Server)

KENAPA SUBDOMAIN, BUKAN PATH:
  cloudflared TIDAK memotong prefix path. Kalau dipakai path '/oo*', permintaan
  '/oo/healthcheck' diteruskan UTUH ke OnlyOffice -> "Cannot GET /oo/healthcheck".
  Jadi editor tidak akan pernah termuat. Subdomain bersih: apa yang diminta
  browser persis sama dengan yang diterima server.

Idempotent: aman dijalankan berulang.
"""
import json
import sys
import urllib.error
import urllib.request

VAULT = '/opt/data/vault/cloudflare.json'
DOMAIN = 'eduai.bikinaja.id'
OO_DOMAIN = 'oo.bikinaja.id'
ZONE = 'bikinaja.id'
APP_TARGET = 'http://172.17.0.9:8000'
OO_TARGET = 'http://172.17.0.7:80'


def ip_container(nama: str) -> str:
    """Ambil IP container dari docker inspect (lewat socket, tanpa docker CLI)."""
    import subprocess
    out = subprocess.run(
        ['docker', 'inspect', nama, '--format',
         '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'],
        capture_output=True, text=True).stdout.strip()
    return out


def api(url, token, method='GET', data=None):
    req = urllib.request.Request(
        url, method=method,
        data=json.dumps(data).encode() if data else None,
        headers={'Authorization': f'Bearer {token}',
                 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        return {'_error': e.code, '_body': e.read().decode()[:400]}


def main():
    v = json.load(open(VAULT))
    token, acc = v['api_token'], v['account_id']

    print('1. Ambil IP container')
    ip_app = ip_container('eduai-app') or '172.17.0.9'
    ip_oo = ip_container('oo-converter') or '172.17.0.7'
    print(f'   eduai-app    -> {ip_app}')
    print(f'   oo-converter -> {ip_oo}')

    print('\n2. Cari zona + tunnel')
    z = api(f'https://api.cloudflare.com/client/v4/zones?name={ZONE}', token)
    zona = (z.get('result') or [{}])[0]
    zone_id = zona.get('id')
    if not zone_id:
        sys.exit(f'❌ zona {ZONE} tidak ditemukan: {json.dumps(z)[:200]}')
    print(f'   zone_id: {zone_id}')

    t = api(f'https://api.cloudflare.com/client/v4/accounts/{acc}/cfd_tunnel', token)
    tunnel_id = None
    for x in t.get('result', []):
        if 'bikinaja' in (x.get('name') or '').lower():
            tunnel_id = x['id']
            break
    if not tunnel_id and t.get('result'):
        tunnel_id = t['result'][0]['id']
    if not tunnel_id:
        sys.exit('❌ tunnel tidak ditemukan')
    print(f'   tunnel_id: {tunnel_id}')

    # ambil domain tunnel (target CNAME)
    dt = api(f'https://api.cloudflare.com/client/v4/accounts/{acc}/cfd_tunnel/{tunnel_id}',
             token)
    cname_target = f'{tunnel_id}.cfargotunnel.com'
    print(f'   CNAME target: {cname_target}')

    print('\n3. Buat/perbarui DNS record')
    for host in (DOMAIN, OO_DOMAIN):
        ada = api(f'https://api.cloudflare.com/client/v4/zones/{zone_id}'
                  f'/dns_records?name={host}', token)
        recs = ada.get('result') or []
        payload = {'type': 'CNAME', 'name': host, 'content': cname_target,
                   'proxied': True, 'ttl': 1,
                   'comment': 'EduAi Publishing (otomatis)'}
        if recs:
            rid = recs[0]['id']
            r = api(f'https://api.cloudflare.com/client/v4/zones/{zone_id}'
                    f'/dns_records/{rid}', token, 'PUT', payload)
            print(f"   {host}: diperbarui {'✅' if r.get('success') else '❌ ' + json.dumps(r)[:150]}")
        else:
            r = api(f'https://api.cloudflare.com/client/v4/zones/{zone_id}'
                    f'/dns_records', token, 'POST', payload)
            print(f"   {host}: dibuat {'✅' if r.get('success') else '❌ ' + json.dumps(r)[:150]}")

    print('\n4. Perbarui aturan tunnel')
    cfg_url = (f'https://api.cloudflare.com/client/v4/accounts/{acc}'
               f'/cfd_tunnel/{tunnel_id}/configurations')
    now = api(cfg_url, token)
    cfg = now.get('result', {}).get('config', {}) or {}
    ingress = cfg.get('ingress') or []

    ingress = [x for x in ingress
               if x.get('hostname') not in (DOMAIN, OO_DOMAIN)]
    catch_all = [x for x in ingress if 'hostname' not in x]
    lain = [x for x in ingress if 'hostname' in x]

    baru = [
        {'hostname': OO_DOMAIN, 'service': f'http://{ip_oo}:80',
         'originRequest': {'disableChunkedEncoding': False}},
        {'hostname': DOMAIN, 'service': f'http://{ip_app}:8000'},
    ] + lain + (catch_all or [{'service': 'http_status:404'}])

    hasil = api(cfg_url, token, 'PUT', {'config': {**cfg, 'ingress': baru}})
    if hasil.get('success'):
        print('   ✅ aturan tunnel diperbarui:')
        for x in baru[:4]:
            if 'hostname' in x:
                print(f"      {x['hostname']} -> {x['service']}")
    else:
        print('   ❌ gagal:', json.dumps(hasil)[:300])
        sys.exit(1)

    print('\n5. Tulis URL editor ke .env')
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent / '.env'
    s = p.read_text(encoding='utf-8')
    s = '\n'.join(l for l in s.splitlines() if not l.startswith('EDUAI_OO_PUBLIC_URL'))
    s += f'\nEDUAI_OO_PUBLIC_URL=https://{OO_DOMAIN}\n'
    p.write_text(s, encoding='utf-8')
    print(f'   EDUAI_OO_PUBLIC_URL=https://{OO_DOMAIN}')
    print('\nSELESAI. Jalankan ulang container agar .env terbaca.')


if __name__ == '__main__':
    main()
