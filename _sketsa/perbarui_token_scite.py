"""Perbarui EDUAI_SCITE_TOKEN + REFRESH di .env dari hasil penyegaran terakhir.

Juga menyimpan token SEGAR ke berkas token Hermes MCP supaya dua-duanya sinkron.
"""
import json
import re
import urllib.parse
import urllib.request

# 1. minta token segar
env = {}
for ln in open('.env'):
    m = re.match(r'^(EDUAI_SCITE\w+)=(.*)$', ln.strip())
    if m:
        env[m.group(1)] = m.group(2)

badan = urllib.parse.urlencode({
    'grant_type': 'refresh_token',
    'refresh_token': env['EDUAI_SCITE_REFRESH'],
    'client_id': env['EDUAI_SCITE_CLIENT_ID']}).encode()
req = urllib.request.Request('https://api.scite.ai/mcp/oauth/token', data=badan,
                             headers={'Content-Type':
                                      'application/x-www-form-urlencoded'})
d = json.load(urllib.request.urlopen(req, timeout=40))
print('token baru ok, berlaku', d.get('expires_in'), 'detik')

# 2. tulis ke .env (ganti baris lama, jangan menumpuk)
s = open('.env').read()
s = re.sub(r'^EDUAI_SCITE_TOKEN=.*$', 'EDUAI_SCITE_TOKEN=' + d['access_token'],
           s, flags=re.M)
s = re.sub(r'^EDUAI_SCITE_REFRESH=.*$', 'EDUAI_SCITE_REFRESH=' + d['refresh_token'],
           s, flags=re.M)
open('.env', 'w').write(s)
print('.env diperbarui')

# 3. simpan juga ke berkas token Hermes MCP (sumber asli)
p = '/opt/data/mcp-tokens/scite.json'
json.dump(d, open(p, 'w'), indent=1)
print('mcp-tokens/scite.json diperbarui')
