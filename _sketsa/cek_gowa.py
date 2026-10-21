"""Cek GOWA dari dalam eduai-app (pakai urllib)."""
import base64
import json
import urllib.request

AUTH = base64.b64encode(b'gowa:sayangku@1').decode()


def get(path, device=None):
    req = urllib.request.Request(
        'http://172.17.0.1:3000' + path,
        headers={'Authorization': 'Basic ' + AUTH,
                 **({'X-Device-Id': device} if device else {})})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode()[:400]
    except Exception as e:
        return type(e).__name__, str(e)[:200]


print('devices:', get('/app/devices'))
print('status :', get('/app/status', 'Gowa'))
