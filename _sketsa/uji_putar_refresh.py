"""Buktikan: apakah refresh_token Scite DIPUTAR (rotate) tiap dipakai?

Kalau ya, .env lama jadi basi ⇒ ini akar 'HTTP 400 Bad Request'.
"""
import json
import re
import urllib.error
import urllib.parse
import urllib.request

env = {}
for ln in open('.env'):
    m = re.match(r'^(EDUAI_SCITE\w+)=(.*)$', ln.strip())
    if m:
        env[m.group(1)] = m.group(2)


def segarkan(rf):
    badan = urllib.parse.urlencode({
        'grant_type': 'refresh_token', 'refresh_token': rf,
        'client_id': env['EDUAI_SCITE_CLIENT_ID']}).encode()
    req = urllib.request.Request(
        'https://api.scite.ai/mcp/oauth/token', data=badan,
        headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {'_err': e.code, '_body': e.read().decode()[:200]}


print('── percobaan 1 dengan refresh di .env ──')
a = segarkan(env['EDUAI_SCITE_REFRESH'])
if '_err' in a:
    print('  GAGAL:', a['_err'], a['_body'][:150])
else:
    print('  ✅ dapat token. refresh BARU sama dgn lama?',
          a.get('refresh_token') == env['EDUAI_SCITE_REFRESH'])
    print('  refresh baru:', (a.get('refresh_token') or '')[:14], '...')
    print()
    print('── percobaan 2: pakai refresh LAMA lagi (kalau rotate → GAGAL) ──')
    b = segarkan(env['EDUAI_SCITE_REFRESH'])
    print('  hasil:', 'GAGAL ' + str(b.get('_err')) if '_err' in b else 'masih boleh')
    if '_err' in b:
        print('  ⇒ TERBUKTI: refresh_token DIPUTAR (rotate).')
        print('     Refresh lama HANGUS setelah dipakai sekali.')
