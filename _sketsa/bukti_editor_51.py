"""Bukti dashboard editor: pakai CDP DOM + target anak (iframe) -> hindari main-thread macet.
Cara: buat tab, navigasi /edit/51, lalu BACA TARGET OO (iframe) dan evaluasi DI DALAMNYA."""
import base64
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import potret_cdp as P                                                   # noqa: E402

DASAR = 'https://eduai.bikinaja.id'
nama = os.environ['EDUAI_COOKIE_NAME']
nilai = os.environ['EDUAI_SESSION']
FID = os.environ.get('EDUAI_FID', '51')


def targets():
    return json.load(urllib.request.urlopen('http://127.0.0.1:9333/json/list', timeout=5))


def tutup_url(patok):
    for t in targets():
        if patok in t.get('url', ''):
            try:
                urllib.request.urlopen('http://127.0.0.1:9333/json/close/' + t['id'],
                                       timeout=5)
                print('  tutup yatim:', t['url'][:60])
            except Exception:                                            # noqa: BLE001
                pass


print('== bersihkan tab yatim ==')
tutup_url('/edit/')
tutup_url('/oo/aset/')
time.sleep(2)

P.bersihkan_tab()
tab, tid = P.tab_baru('about:blank')
try:
    tab.cmd('Page.enable')
    tab.cmd('Network.setCookie', {'name': nama, 'value': nilai,
                                  'url': DASAR, 'path': '/'})
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': 1400, 'height': 1000, 'deviceScaleFactor': 1,
             'mobile': False})
    tab.cmd('Page.navigate', {'url': DASAR + '/edit/' + FID})
    print('== navigasi, tunggu 50 dtk ==')
    time.sleep(50)
finally:
    pass

# Cari target OO (iframe editor) lewat /json/list
print('== target OO ditemukan ==')
oo = None
for t in targets():
    u = t.get('url', '')
    if '/oo/aset/' in u or 'documenteditor' in u or 'apps/documenteditor' in u:
        oo = t
        print('  ', u[:90])
if not oo:
    print('  (belum ada target OO) — halaman induk mungkin belum menyematkan iframe')

# Potret dari tab utama
try:
    r = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=60)
    data = r.get('result', {}).get('data')
    if data:
        with open('/tmp/editor_oo5.png', 'wb') as f:
            f.write(base64.b64decode(data))
        print('png:', os.path.getsize('/tmp/editor_oo5.png'), 'byte')
except Exception as ex:                                                  # noqa: BLE001
    print('potret gagal:', str(ex)[:80])

# Baca modal galat dari tab utama via DOM.getDocument (bukan Runtime)
try:
    doc = tab.cmd('DOM.getDocument', {'depth': 2}, timeout=30)
    letak = doc.get('result', {}).get('root', {}).get('nodeId')
    q = tab.cmd('DOM.querySelectorAll',
                {'nodeId': letak, 'selector': '#galat'}, timeout=30)
    print('node #galat:', q.get('result', {}).get('nodeIds'))
except Exception as ex:                                                  # noqa: BLE001
    print('DOM cek gagal:', str(ex)[:80])

try:
    tab.tutup()
except Exception:                                                        # noqa: BLE001
    pass
