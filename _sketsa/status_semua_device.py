"""Status semua device GOWA yang punya JID."""
import base64
import json
import urllib.request

AUTH = base64.b64encode(b'gowa:sayangku@1').decode()
BASE = 'http://172.17.0.1:3000'


def status(dev):
    req = urllib.request.Request(
        BASE + '/app/status',
        headers={'Authorization': 'Basic ' + AUTH, 'X-Device-Id': dev})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode()).get('results', {})
    except Exception as e:
        return {'galat': str(e)[:60]}


for d in ('Gowa', 'OJS%20Tridarma.id', 'OJS%20Tridarma.id/log'):
    r = status(d)
    print(f"{d} → connected={r.get('is_connected')} "
          f"logged_in={r.get('is_logged_in')} jid={r.get('jid','-')}")
