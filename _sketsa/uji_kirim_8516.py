"""Coba kirim WA dari device yang sesinya hidup:
1. X-Device-Id mentah dgn slash (Go router mungkin baca sisa path)
2. Trailing-slash trick: /send/message/ + device sebagai segmen?
3. Header X-Device-Id dgn %20 ter-decode (OJS Tridarma.id/log mentah).
"""
import base64
import json
import urllib.request

AUTH = base64.b64encode(b'gowa:sayangku@1').decode()
BASE = 'http://172.17.0.1:3000'
ISI = 'Uji kirim — pengirim 6285178138516 (Tridarma.id User).'


def coba(label, path, dev):
    h = {'Authorization': 'Basic ' + AUTH,
         'Content-Type': 'application/json',
         'X-Device-Id': dev}
    r = urllib.request.Request(
        BASE + path, headers=h,
        data=json.dumps({'phone': '6285720505555@s.whatsapp.net',
                         'message': ISI}).encode(),
        method='POST')
    try:
        with urllib.request.urlopen(r, timeout=25) as resp:
            print(label, '→', resp.status, resp.read().decode()[:150])
            return True
    except Exception as e:
        isi = ''
        if hasattr(e, 'read'):
            try:
                isi = e.read().decode()[:110]
            except Exception:
                pass
        print(label, '→', str(e)[:60], isi)
        return False


# 1: device mentah dengan slash & spasi persis seperti di DB
coba('mentah spasi+slash', '/send/message', 'OJS Tridarma.id/log')
# 2: tanpa decode (%20 apa adanya)
coba('encoded %20', '/send/message', 'OJS%20Tridarma.id/log')
# 3: devicename saja tanpa /log
coba('tanpa /log', '/send/message', 'OJS Tridarma.id')
