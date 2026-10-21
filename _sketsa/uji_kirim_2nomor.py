"""Kirim 1 pesan uji dari 2 nomor Tridarma ke nomor Bos."""
import base64
import json
import urllib.request

AUTH = base64.b64encode(b'gowa:sayangku@1').decode()
BASE = 'http://172.17.0.1:3000'
TUJUAN = '6285720505555@s.whatsapp.net'

for dev, isi in (
    ('OJS%20Tridarma.id',
     'Uji 1 — pengirim 6285178138514 (Tridarma Published). '
     'Kalau pesan ini masuk, nomor ini siap jadi pengirim WA EduAi.'),
    ('OJS%20Tridarma.id/log',
     'Uji 2 — pengirim 6285178138516 (Tridarma.id User). '
     'Kalau pesan ini masuk, nomor ini juga hidup.'),
):
    req = urllib.request.Request(
        BASE + '/send/message',
        data=json.dumps({'phone': TUJUAN, 'message': isi}).encode(),
        headers={'Authorization': 'Basic ' + AUTH,
                 'X-Device-Id': dev,
                 'Content-Type': 'application/json'},
        method='POST')
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(dev, '→', r.status, r.read().decode()[:160])
    except Exception as e:
        isi_err = ''
        if hasattr(e, 'read'):
            try:
                isi_err = e.read().decode()[:200]
            except Exception:
                pass
        print(dev, '→ GALAT:', str(e)[:80], isi_err)
