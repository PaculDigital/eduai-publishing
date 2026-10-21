#!/usr/bin/env python3
"""Tekan 'Mulai uji' di /plagiarisme (LIVE) → potret proses → potret hasil.

Mengikuti alur user asli: login akun uji → pilih naskah → centang gratis →
tekan Mulai uji → tunggu → potret.
"""
import base64
import json
import time
import urllib.request

import websocket

CDP = 'http://127.0.0.1:9333'
DOMAIN = 'eduai.bikinaja.id'
EMAIL = 'uji-potret-plag16okt@eduai.test'
SANDI = 'ujiPotret16Okt2026'


def tab_baru():
    r = urllib.request.Request(CDP + '/json/new?about:blank', method='PUT')
    return json.loads(urllib.request.urlopen(r, timeout=20).read())


class Halaman:
    def __init__(self):
        t = tab_baru()
        self.ws = websocket.create_connection(
            t['webSocketDebuggerUrl'], timeout=180,
            suppress_origin=True, max_size=80 * 1024 * 1024)
        self.n = 0
        self.kirim('Page.enable')
        self.kirim('Runtime.enable')
        self.kirim('Emulation.setDeviceMetricsOverride', width=430, height=1600,
                   deviceScaleFactor=2, mobile=True)

    def kirim(self, method, **p):
        self.n += 1
        self.ws.send(json.dumps({'id': self.n, 'method': method, 'params': p}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get('id') == self.n:
                return m

    def nilai(self, expr, tunggu_janji=False):
        r = self.kirim('Runtime.evaluate', expression=expr, returnByValue=True,
                       awaitPromise=tunggu_janji)
        res = r.get('result', {}).get('result', {})
        return res.get('value', res)

    def buka(self, path, t=4):
        self.kirim('Page.navigate', url=f'https://{DOMAIN}{path}')
        time.sleep(t)

    def potret(self, keluar):
        r = self.kirim('Page.captureScreenshot', format='png',
                       captureBeyondViewport=True)
        open(keluar, 'wb').write(base64.b64decode(r['result']['data']))
        return keluar


h = Halaman()
print('  ① login')
h.buka('/masuk', 3)
for sel, val in (("input[name=email]", EMAIL), ("input[name=password]", SANDI)):
    h.nilai("(() => {const e=document.querySelector(%s); e.focus();"
            " e.value=%s; e.dispatchEvent(new Event('input',"
            "{bubbles:true}));})()" % (json.dumps(sel), json.dumps(val)))
h.nilai("document.querySelector('button[type=submit]').click()")
time.sleep(4)
print('     url:', h.nilai('location.pathname'))

print('  ② buka /plagiarisme, pilih naskah, centang gratis')
h.buka('/plagiarisme', 5)
print('     pilihan naskah:', h.nilai(
    "JSON.stringify([...document.querySelectorAll('select option')]"
    ".map(o=>o.textContent.trim()))"))
h.nilai("""(() => {const s=document.querySelector('select');
    s.selectedIndex=1; s.dispatchEvent(new Event('change',
    {bubbles:true})); return s.value;})()""")
time.sleep(1)
print('     dicentang gratis:', h.nilai(
    "(() => {const c=document.querySelector('input[type=checkbox]');"
    " if(c && !c.checked) c.click(); return c ? c.checked : null;})()"))
h.potret('/tmp/alur_1_siap.png')
print('     ✓ /tmp/alur_1_siap.png (siap tekan)')

print('  ③ TEKAN Mulai uji')
print('     tekan:', h.nilai(
    "(() => {const b=[...document.querySelectorAll('button')]"
    ".find(x=>/mulai uji/i.test(x.textContent));"
    " if(!b) return 'TIDAK ADA'; b.click(); return 'DITEKAN';})()"))
time.sleep(3)
h.potret('/tmp/alur_2_proses.png')
print('     ✓ /tmp/alur_2_proses.png (proses)')
print('     isi layar:', h.nilai('document.body.innerText')[-700:])

print('  ④ tunggu selesai (maks 150 dtk)')
selesai = False
for i in range(30):
    time.sleep(5)
    teks = h.nilai('document.body.innerText')
    if 'unduh' in teks.lower() or 'pratinjau' in teks.lower() and 'tidak' not in teks.lower()[-200:]:
        selesai = True
        print(f'     ✔ sinyal hasil muncul di detik {(i+1)*5}')
        break
    if 'gagal' in teks.lower() or 'error' in teks.lower():
        print('     ✗ sinyal GAGAL muncul')
        break
h.potret('/tmp/alur_3_hasil.png')
print('     ✓ /tmp/alur_3_hasil.png · selesai:', selesai)
print('     isi akhir:', h.nilai('document.body.innerText')[-800:])
