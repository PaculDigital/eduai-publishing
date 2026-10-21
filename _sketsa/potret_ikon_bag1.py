"""SUNTIK SESI — bikin token login sah dari SECRET_KEY, pasang ke Chrome.

KENAPA: potret layar butuh login, tapi Wulan tidak menyimpan password apa pun
(aturan: jangan simpan sandi). Token sesi dibuat memakai fungsi app yang SAMA
(`buat_token`) supaya yang diuji benar-benar alur aslinya.
"""
import json, sys, time, os, base64, urllib.request, subprocess
from websocket import create_connection

BASE = 'https://eduai.bikinaja.id'
CDP = 'http://127.0.0.1:9341'
OUT = '/opt/data/services/eduai-publishing/_potret/sketsa-ikon'
os.makedirs(OUT, exist_ok=True)

#  ── 1. bikin token sesi untuk user 3 (akun uji) ─────────────────────
kode = (
    "from app.auth import buat_token\n"
    "from app.config import SESSION_COOKIE\n"
    "print(SESSION_COOKIE + '|' + buat_token(3))\n"
)
r = subprocess.run(['docker', 'exec', '-w', '/app', 'eduai-app', 'python3', '-c', kode],
                   capture_output=True, text=True, timeout=90)
if r.returncode != 0:
    print('GAGAL bikin token:', r.stderr[-400:]); sys.exit(1)
NAMA_COOKIE, TOKEN = r.stdout.strip().split('|', 1)
print(f'cookie: {NAMA_COOKIE}  token: {TOKEN[:16]}… ({len(TOKEN)} kar)')


def tab_baru(url='about:blank'):
    req = urllib.request.Request(CDP + '/json/new?' + url, method='PUT')
    for _ in range(25):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=8).read())
        except Exception:
            time.sleep(1)
    raise SystemExit('CDP tidak menjawab')


t = tab_baru()
ws = create_connection(t['webSocketDebuggerUrl'], timeout=90)
_id = [0]


def cmd(m, **p):
    _id[0] += 1
    ws.send(json.dumps({'id': _id[0], 'method': m, 'params': p}))
    while True:
        d = json.loads(ws.recv())
        if d.get('id') == _id[0]:
            return d.get('result', {})


def js(e):
    res = cmd('Runtime.evaluate', expression=e, awaitPromise=True,
              returnByValue=True)
    return res.get('result', {}).get('value')


def potret(nama):
    res = cmd('Page.captureScreenshot', format='png', captureBeyondViewport=True)
    d = res.get('data', '')
    if not d:
        print('  ✗ potret kosong'); return None
    p = os.path.join(OUT, nama)
    open(p, 'wb').write(base64.b64decode(d))
    print(f'  ✓ {nama} ({os.path.getsize(p)} byte)')
    return p


cmd('Page.enable'); cmd('Runtime.enable')
cmd('Network.enable')
cmd('Emulation.setDeviceMetricsOverride', width=1180, height=1500,
    deviceScaleFactor=1, mobile=False)

#  ── 2. pasang cookie sesi (domain + path benar untuk HTTPS) ─────────
hasil = cmd('Network.setCookie', name=NAMA_COOKIE, value=TOKEN,
            domain='eduai.bikinaja.id', path='/', secure=True, httpOnly=True)
print('pasang cookie:', hasil)
js(f"location.href='{BASE}/naskah'")
time.sleep(7)
print('url  :', js('location.href'))
print('judul:', js('document.title'))
