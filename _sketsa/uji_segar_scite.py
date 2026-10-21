"""Uji PENYEGARAN token Scite: pakai refresh_token → dapat access_token baru.

Jalankan DI HOST (bukan container) dengan .env dimuat.
"""
import json
import os
import re
import urllib.parse
import urllib.request

for ln in open('.env'):
    m = re.match(r'^(EDUAI_SCITE\w+)=(.*)$', ln.strip())
    if m:
        os.environ[m.group(1)] = m.group(2)

rf = os.environ.get('EDUAI_SCITE_REFRESH', '')
cid = os.environ.get('EDUAI_SCITE_CLIENT_ID', '')
print('refresh ada:', bool(rf), '| client_id:', cid)

badan = urllib.parse.urlencode({'grant_type': 'refresh_token',
                                'refresh_token': rf,
                                'client_id': cid}).encode()
req = urllib.request.Request('https://api.scite.ai/mcp/oauth/token', data=badan,
                             headers={'Content-Type':
                                      'application/x-www-form-urlencoded'})
try:
    with urllib.request.urlopen(req, timeout=40) as r:
        d = json.load(r)
    print('✅ token BARU didapat')
    print('   kunci:', sorted(d.keys()))
    print('   berlaku:', d.get('expires_in'), 'detik')
    tok = d['access_token']
    # uji pakai token baru
    def rpc(method, params, rid=1):
        b = json.dumps({'jsonrpc': '2.0', 'id': rid, 'method': method,
                        'params': params}).encode()
        q = urllib.request.Request('https://api.scite.ai/mcp', data=b, headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
            'Authorization': 'Bearer ' + tok})
        raw = urllib.request.urlopen(q, timeout=60).read().decode()
        for ln2 in raw.splitlines():
            s2 = ln2.strip()
            if s2.startswith('data:'):
                s2 = s2[5:].strip()
            if s2.startswith('{'):
                return json.loads(s2)
        return json.loads(raw)
    rpc('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {},
                       'clientInfo': {'name': 'uji', 'version': '1.0'}})
    res = rpc('tools/call', {'name': 'search_literature',
                             'arguments': {'dois': ['10.5465/amr.2000.2791609'],
                                           'limit': 1}}, rid=2)
    teks = ''.join(c.get('text', '')
                   for c in ((res.get('result') or {}).get('content') or []))
    j = json.loads(teks) if teks.strip().startswith('{') else {}
    hits = j.get('hits') or []
    print('   hits:', len(hits), '| citations:',
          len((hits[0].get('citations') or []) if hits else []))
except Exception as ex:
    print('❌ GAGAL:', str(ex)[:300])
