"""Debug kenapa /kolaborasi masih minta login: tanam cookie → buka → baca."""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import potret_cdp as P                                              # noqa: E402

DASAR = 'https://eduai.bikinaja.id'
nama = os.environ['EDUAI_COOKIE_NAME']
nilai = os.environ['EDUAI_SESSION']

tab, tid = P.tab_baru('about:blank')
try:
    tab.cmd('Network.enable')
    r = tab.cmd('Network.setCookie',
                {'name': nama, 'value': nilai, 'url': DASAR, 'path': '/'})
    print('setCookie      :', json.dumps(r.get('result')))
    tab.cmd('Page.enable')
    tab.cmd('Page.navigate', {'url': DASAR + '/kolaborasi'})
    time.sleep(6)
    ev = tab.cmd('Runtime.evaluate', {
        'expression': ('JSON.stringify({href: location.href, '
                       'cookie: document.cookie, '
                       'isi: document.body.innerText.slice(0,300)})'),
        'returnByValue': True}, timeout=30)
    print('halaman        :', ev.get('result', {}).get('result', {}).get('value'))
    #  buktikan cookie BENAR-BENAR terkirim ke server
    tab.cmd('Page.navigate', {'url': DASAR + '/api/cek-sesi'})
    time.sleep(3)
    ev2 = tab.cmd('Runtime.evaluate', {
        'expression': ('JSON.stringify({href: location.href, '
                       'isi: document.body.innerText.slice(0,300)})'),
        'returnByValue': True}, timeout=30)
    print('api/cek-sesi   :', ev2.get('result', {}).get('result', {}).get('value'))
finally:
    try:
        urllib.request.urlopen(f'{P.CDP}/json/close/{tid}', timeout=5).read()
    except Exception:                                               # noqa: BLE001
        pass
    tab.tutup()
