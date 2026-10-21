"""Buat ulang device + pair code untuk 2 nomor Tridarma."""
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
            return resp.status, resp.read().decode()[:300]
    except Exception as e:
        isi = ''
        if hasattr(e, 'read'):
            try:
                isi = e.read().decode()[:200]
            except Exception:
                pass
        return 'ERR', f'{str(e)[:80]} {isi}'


# 8514: device ada tapi session deleted → hapus slot lama, buat baru
print('hapus 8514:', req('/devices/OJS%20Tridarma.id',
                         'OJS%20Tridarma.id', method='DELETE'))
print('buat 8514:', req('/api/devices', 'eduai-wa-8514', json.dumps(
    {'device_id': 'eduai-wa-8514'}).encode(), 'POST'))
print('pair 8514:', req(
    '/app/login-with-code?phone=6285178138514', 'eduai-wa-8514'))

# 8516: device path '/log' tidak dikenal API → buat device bersih
print('buat 8516:', req('/api/devices', 'eduai-wa-8516', json.dumps(
    {'device_id': 'eduai-wa-8516'}).encode(), 'POST'))
print('pair 8516:', req(
    '/app/login-with-code?phone=6285178138516', 'eduai-wa-8516'))
