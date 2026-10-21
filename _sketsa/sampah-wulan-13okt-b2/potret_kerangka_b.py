"""Potret panel kerangka `/mulai` — bukti AI memakai artikel naskah.

Orde resmi CDP: Tab('about:blank') → Page.enable → setDeviceMetrics →
Network.setCookie → Page.navigate. Baca innerText.
"""
import base64
import json
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa/sampah-wulan-13okt-sambunganA')
from ws_mentah import WS                                     # noqa: E402

CDP = 'http://127.0.0.1:9333'
URL = 'http://172.17.0.8:8000/mulai'
KELUAR = '/opt/data/kerangka_b.png'
LEBAR, TINGGI = 430, 1500

kode = ("from app.auth import buat_token\nfrom app.config import SESSION_COOKIE\n"
        "print(SESSION_COOKIE + '|' + buat_token(9))\n")
r = subprocess.run(['docker', 'exec', '-w', '/app', 'eduai-app',
                    'python3', '-c', kode],
                   capture_output=True, text=True, timeout=90)
nama, token = r.stdout.strip().split('|', 1)
print(f'kuki {nama} · user 9')

#  tab baru (WAJIB PUT)
req = urllib.request.Request(f'{CDP}/json/new?about:blank', method='PUT')
with urllib.request.urlopen(req, timeout=15) as f:
    tab = json.loads(f.read().decode())
ws_url = tab['webSocketDebuggerUrl']
print('tab:', tab['id'])

ws = WS(ws_url)
ws.cmd('Page.enable')
time.sleep(0.4)
ws.cmd('Network.enable')
time.sleep(0.4)
ws.cmd('Emulation.setDeviceMetricsOverride', width=LEBAR, height=TINGGI,
         deviceScaleFactor=2, mobile=True)
time.sleep(0.4)
ws.cmd('Network.setCookie', name=nama, value=token, domain='172.17.0.8',
         path='/')
time.sleep(0.4)
ws.cmd('Page.navigate', url=URL)
print('navigasi... tunggu 9 dtk')
time.sleep(9)

teks = (ws.cmd('Runtime.evaluate', expression='document.body.innerText',
               returnByValue=True).get('result', {})
        .get('result', {}).get('value') or '')
print(f'\ninnerText {len(teks)} karakter')
print('── 900 char pertama ──')
print(teks[:900])

#  simpan
shot = ws.cmd('Page.captureScreenshot', format='png',
                captureBeyondViewport=True)
data = shot.get('result', {}).get('data')
if data:
    with open(KELUAR, 'wb') as f:
        f.write(base64.b64decode(data))
    print(f'\n✅ {KELUAR} — {len(base64.b64decode(data))} byte')
else:
    print('\n❌ potret gagal:', str(shot)[:200])
ws.finish() if hasattr(ws,'finish') else None
