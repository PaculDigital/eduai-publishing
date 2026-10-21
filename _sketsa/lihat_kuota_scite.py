"""Tampilkan KUOTA Scite (dari tool resmi manage_subscription)."""
import json
import sys
import urllib.request
sys.path.insert(0, '/app')
from app.pustaka import _scite_token_segar

t = _scite_token_segar()
b = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                'params': {'name': 'manage_subscription',
                           'arguments': {'action': 'view'}}}).encode()
q = urllib.request.Request('https://api.scite.ai/mcp', data=b, headers={
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/event-stream',
    'Authorization': 'Bearer ' + t})
raw = urllib.request.urlopen(q, timeout=45).read().decode()
d = None
for ln in raw.splitlines():
    s = ln.strip()[5:].strip() if ln.strip().startswith('data:') else ln.strip()
    if s.startswith('{'):
        d = json.loads(s)
        break
teks = ''.join(c.get('text', '')
               for c in ((d.get('result') or {}).get('content') or []))
print('=== ISI MENTAH ===')
print(teks[:1200])
try:
    j = json.loads(teks)
    print()
    print('=== RAPI ===')
    for k in ('plan', 'plan_allowance', 'used', 'remaining', 'limit',
              'resets_at', 'subscription_status'):
        if k in j:
            print('  %-20s %s' % (k, j[k]))
except Exception:
    pass
