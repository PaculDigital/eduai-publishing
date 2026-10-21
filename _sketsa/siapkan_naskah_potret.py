#!/usr/bin/env python3
"""Siapkan akun uji + unggah 1 naskah lewat PINTU NYATA (/unggah), lalu potret.

Tidak menyentuh DB produksi secara langsung (kecuali baca email akun uji).
"""
import base64
import json
import mimetypes
import sys
import time
import urllib.request
import uuid

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
            t['webSocketDebuggerUrl'], timeout=120,
            suppress_origin=True, max_size=80 * 1024 * 1024)
        self.n = 0
        self.kirim('Page.enable')
        self.kirim('Runtime.enable')

    def kirim(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({'id': self.n, 'method': method,
                                 'params': params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get('id') == self.n:
                return m

    def nilai(self, expr, await_promise=False):
        r = self.kirim('Runtime.evaluate', expression=expr,
                       returnByValue=True, awaitPromise=await_promise)
        res = r.get('result', {}).get('result', {})
        if 'value' in res:
            return res['value']
        return res

    def buka(self, path, tunggu=4):
        self.kirim('Page.navigate', url=f'https://{DOMAIN}{path}')
        time.sleep(tunggu)

    def potret(self, keluar):
        r = self.kirim('Page.captureScreenshot', format='png',
                       captureBeyondViewport=True)
        open(keluar, 'wb').write(base64.b64decode(r['result']['data']))
        return keluar


h = Halaman()

print('  ① login sebagai akun uji')
h.buka('/masuk', 3)
print('     judul:', h.nilai('document.title'))
h.nilai("""(() => {const e=document.querySelector('input[name=email]');
    e.focus(); e.value=%s; e.dispatchEvent(new Event('input',
    {bubbles:true}));})()""" % json.dumps(EMAIL))
h.nilai("""(() => {const e=document.querySelector('input[name=password]');
    e.focus(); e.value=%s; e.dispatchEvent(new Event('input',
    {bubbles:true}));})()""" % json.dumps(SANDI))
h.nilai("document.querySelector('button[type=submit]').click()")
time.sleep(4)
print('     url  :', h.nilai('location.pathname'))

print('  ② unggah naskah lewat PINTU /unggah')
isi = open('/tmp/naskah_panjang.txt', encoding='utf-8').read() \
    if __import__('os').path.exists('/tmp/naskah_panjang.txt') else None
if isi is None:
    print('     ✗ /tmp/naskah_panjang.txt tidak ada')
    sys.exit(1)
open('/tmp/naskah-potret.docx', 'wb').write(b'')
import zipfile
with zipfile.ZipFile('/tmp/naskah-potret.docx', 'w') as z:
    z.writestr('word/document.xml',
               '<w:document><w:body>'
               + ''.join('<w:p><w:r><w:t>' + p + '</w:t></w:r></w:p>'
                         for p in isi.split('\n') if p.strip())
               + '</w:body></w:document>')
print('     berkas uji siap:',
      __import__('os').path.getsize('/tmp/naskah-potret.docx'), 'byte')

#  unggah via fetch di dalam halaman (form asli) — pakai DataTransfer
js = """
(async () => {
  const b64 = await (await fetch('/static/ikon-burung-about.png')).blob();
  return 'siap';
})()
"""
print('     (pakai Input.setFileInputFiles dari CDP)')
doc = h.kirim('DOM.getDocument')['result']['root']['nodeId']
sel = h.kirim('DOM.querySelector',
              nodeId=doc, selector='#form-unggah input[type=file]')
nid = sel['result']['nodeId']
print('     nodeId input file:', nid)
h.kirim('DOM.setFileInputFiles', nodeId=nid,
        files=['/tmp/naskah-potret.docx'])
time.sleep(1)
print('     kirim form:', h.nilai(
    "(() => {document.getElementById('form-unggah')"
    ".dispatchEvent(new Event('submit',{cancelable:true}));"
    "document.querySelector('#form-unggah button[type=submit]')"
    "?.click(); return 'OK';})()"))
time.sleep(8)
h.buka('/plagiarisme', 5)
print('  ③ isi halaman /plagiarisme:')
print(h.nilai('document.body.innerText')[:1200])
h.potret('/tmp/potret_plag_adanaskah.png')
print('  ✓ potret: /tmp/potret_plag_adanaskah.png')
