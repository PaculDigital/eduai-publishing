"""Daftar device GOWA + status login masing-masing."""
import base64
import json
import urllib.request

AUTH = base64.b64encode(b'gowa:sayangku@1').decode()
BASE = 'http://172.17.0.1:3000'


def get(path, device=None):
    h = {'Authorization': 'Basic ' + AUTH}
    if device:
        h['X-Device-Id'] = device
    req = urllib.request.Request(BASE + path, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {'galat': str(e)[:120]}


# device list butuh X-Device-Id — coba pakai device yang diketahui
daftar = get('/app/devices', 'Gowa')
print('== daftar device ==')
hasil = daftar.get('results', daftar)
if isinstance(hasil, dict):
    hasil = hasil.get('data', [hasil])
for d in hasil if isinstance(hasil, list) else [hasil]:
    print(json.dumps(d, ensure_ascii=False)[:200])

for did in ('Gowa',):
    s = get('/app/status', did)
    r = s.get('results', {})
    print(f"\n{did}: connected={r.get('is_connected')} "
          f"logged_in={r.get('is_logged_in')} jid={r.get('jid','-')}")
