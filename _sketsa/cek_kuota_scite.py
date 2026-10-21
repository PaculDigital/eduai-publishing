"""Cek: apakah Scite balas 0 hits karena KUOTA, atau karena sebab lain?"""
import json
import sys
import urllib.request
import urllib.error
sys.path.insert(0, '/app')
from app.pustaka import _scite_token

tok = _scite_token()
print('token panjang:', len(tok or ''))


def rpc(method, params, rid=1):
    body = json.dumps({'jsonrpc': '2.0', 'id': rid, 'method': method,
                       'params': params}).encode()
    req = urllib.request.Request('https://api.scite.ai/mcp', data=body, headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
        'Authorization': 'Bearer ' + tok})
    try:
        r = urllib.request.urlopen(req, timeout=45)
        return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


st, isi = rpc('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {},
                             'clientInfo': {'name': 'cek', 'version': '1.0'}})
print('initialize →', st)
st, isi = rpc('tools/call', {'name': 'manage_subscription',
                             'arguments': {'action': 'view'}}, rid=2)
print('manage_subscription →', st)
print(isi[:900])
