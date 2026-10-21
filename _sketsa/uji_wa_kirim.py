"""Uji kirim WA via GOWA device 'Gowa' (dari dalam eduai-app)."""
import base64
import json
import urllib.request

AUTH = base64.b64encode(b'gowa:sayangku@1').decode()
req = urllib.request.Request(
    'http://172.17.0.1:3000/send/message',
    data=json.dumps({
        'phone': '6285720505555@s.whatsapp.net',
        'message': 'Uji kirim dari EduAi app (27Sep26) — abaikan pesan ini ya.',
    }).encode(),
    headers={'Authorization': 'Basic ' + AUTH,
             'X-Device-Id': 'Gowa',
             'Content-Type': 'application/json'},
    method='POST')
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        print(r.status, r.read().decode()[:300])
except Exception as e:
    print('GALAT:', type(e).__name__, str(e)[:300],
          getattr(e, 'read', lambda: b'')().decode()[:200])
