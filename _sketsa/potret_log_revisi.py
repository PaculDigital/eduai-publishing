"""POTRET Log Revisi pembimbing di sisi MAHASISWA (halaman /naskah)."""
import json, sys, time, base64, os, urllib.request, urllib.parse
from websocket import create_connection

BASE = 'https://eduai.bikinaja.id'
PW = sys.argv[1]
CDP = 'http://127.0.0.1:9333'


def kirim(ws, mid, method, params=None):
    ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
    while True:
        d = json.loads(ws.recv())
        if d.get('id') == mid:
            return d


def nilai(ws, mid, expr):
    r = kirim(ws, mid, 'Runtime.evaluate',
              {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
    if 'exceptionDetails' in r.get('result', {}):
        return 'JS ERROR: ' + str(r['result']['exceptionDetails'])[:250]
    return r.get('result', {}).get('result', {}).get('value')


_req = urllib.request.Request(
    CDP + '/json/new?' + urllib.parse.quote(BASE + '/naskah', safe=''), method='PUT')
tab = json.loads(urllib.request.urlopen(_req, timeout=20).read())
ws = create_connection(tab['webSocketDebuggerUrl'], timeout=90)
kirim(ws, 1, 'Page.enable'); kirim(ws, 2, 'Runtime.enable')
time.sleep(3)
for c in range(3):
    h = nilai(ws, 10 + c, """
    (function(){
      var e=document.querySelector('input[name=email]')||document.querySelector('input[type=email]');
      var p=document.querySelector('input[name=password]')||document.querySelector('input[type=password]');
      if(!e||!p) return 'SIAP';
      e.value='wulan@bikinaja.me'; p.value=%r; e.closest('form').submit(); return 'SUBMIT';
    })()""" % PW)
    if h == 'SIAP':
        break
    time.sleep(3)
time.sleep(5)
kirim(ws, 20, 'Page.navigate', {'url': f'{BASE}/naskah'})
time.sleep(7)

# klik "Bagikan ke Pembimbing" (bukan yang "lain")
print(nilai(ws, 30, """
(async function(){
  var b=[...document.querySelectorAll('button,a,div[role=button]')]
    .filter(x=>/^Bagikan ke [Pp]embimbing$/.test((x.innerText||'').trim()));
  if(!b.length) return 'TOMBOL TIDAK ADA';
  b[0].click();
  await new Promise(r=>setTimeout(r,3500));
  return document.body.innerText.slice(0,2500);
})()"""))

# cari tombol Log Revisi / panah pembimbing
print('\n══ CARI & BUKA LOG REVISI ══')
print(nilai(ws, 40, """
(async function(){
  var semua=[...document.querySelectorAll('button,a,div,span')]
    .filter(x=>/Log Revisi/i.test((x.innerText||'').trim()) && x.innerText.trim().length<40);
  if(!semua.length) return 'Log Revisi TIDAK ADA. Tombol terlihat: '
      + [...document.querySelectorAll('button')].map(b=>b.innerText.trim()).slice(0,25).join(' | ');
  semua[0].click();
  await new Promise(r=>setTimeout(r,3000));
  var t=document.body.innerText||''; var i=t.indexOf('Log Revisi');
  return t.slice(Math.max(0,i-200), i+1500);
})()"""))

r = kirim(ws, 50, 'Page.captureScreenshot',
          {'format': 'png', 'captureBeyondViewport': True})
out = '/tmp/mhs_log_revisi.png'
open(out, 'wb').write(base64.b64decode(r['result']['data']))
print(f'\npotret: {out} · {os.path.getsize(out):,} byte')
ws.close()
print('PATH_POTRET=' + out)
