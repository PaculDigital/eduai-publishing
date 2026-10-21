"""Buat device eduai-wa-8516 + pair code untuk KEDUA nomor (endpoint /devices)."""
import base64
import json
import urllib.request

AUTH = base64.b64encode(b'gowa:sayangku@1').decode()
BASE = 'http://172.17.0.1:3000'


def req(path, dev=None, data=None, method=None):
    h = {'Authorization': 'Basic ' + AUTH, 'Content-Type': 'application/json'}
    if dev:
        h['X-Device-Id'] = dev
    r = urllib.request.Request(BASE + path, headers=h, data=data,
                               method=method)
    try:
        with urllib.request.urlopen(r, timeout=25) as resp:
            return resp.status, resp.read().decode()[:260]
    except Exception as e:
        isi = ''
        if hasattr(e, 'read'):
            try:
                isi = e.read().decode()[:160]
            except Exception:
                pass
        return 'ERR', f'{str(e)[:70]} {isi}'


print('buat 8516:', req('/devices', 'eduai-wa-8516', json.dumps(
    {'device_id': 'eduai-wa-8516'}).encode(), 'POST'))
print('pair 8514:', req('/app/login-with-code?phone=6285178138514',
                        'eduai-wa-8514'))
print('pair 8516:', req('/app/login-with-code?phone=6285178138516',
                        'eduai-wa-8516'))
