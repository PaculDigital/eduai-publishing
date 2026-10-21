"""Reconnect 2 nomor Tridarma lalu kirim ulang pesan uji."""
import base64
import json
import time
import urllib.request

AUTH = base64.b64encode(b'gowa:sayangku@1').decode()
BASE = 'http://172.17.0.1:3000'
TUJUAN = '6285720505555@s.whatsapp.net'


def req(path, dev=None, data=None, method=None):
    h = {'Authorization': 'Basic ' + AUTH, 'Content-Type': 'application/json'}
    if dev:
        h['X-Device-Id'] = dev
    r = urllib.request.Request(BASE + path, headers=h, data=data,
                               method=method)
    try:
        with urllib.request.urlopen(r, timeout=25) as resp:
            return resp.status, resp.read().decode()[:200]
    except Exception as e:
        isi = ''
        if hasattr(e, 'read'):
            try:
                isi = e.read().decode()[:200]
            except Exception:
                pass
        return 'ERR', f'{str(e)[:80]} {isi}'


print('== reconnect ==')
print('8514:', req('/app/reconnect', 'OJS%20Tridarma.id'))
print('8516:', req('/app/reconnect', 'OJS%20Tridarma.id/log'))

time.sleep(8)
print('== status ==')
print('8514:', req('/app/status', 'OJS%20Tridarma.id'))
print('8516:', req('/app/status', 'OJS%20Tridarma.id/log'))

print('== kirim ==')
print('8514:', req('/send/message', 'OJS%20Tridarma.id', json.dumps(
    {'phone': TUJUAN,
     'message': 'Uji 1 — pengirim 6285178138514 (Tridarma Published). '
                'Kalau masuk, nomor ini siap jadi pengirim WA EduAi.'}
).encode(), 'POST'))
print('8516:', req('/send/message', 'OJS%20Tridarma.id/log', json.dumps(
    {'phone': TUJUAN,
     'message': 'Uji 2 — pengirim 6285178138516 (Tridarma.id User). '
                'Kalau masuk, nomor ini juga hidup.'}
).encode(), 'POST'))
