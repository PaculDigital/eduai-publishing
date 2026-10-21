"""POTRET halaman MAHASISWA — daftar naskah + Log Revisi pembimbing."""
import json, sys, time, base64, subprocess, os, urllib.request, urllib.parse
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
    res = r.get('result', {}).get('result', {})
    if res.get('subtype') == 'error' or 'exceptionDetails' in r.get('result', {}):
        return 'JS ERROR: ' + str(r.get('result', {}).get('exceptionDetails', {}))[:200]
    return res.get('value')


_req = urllib.request.Request(
    CDP + '/json/new?' + urllib.parse.quote(BASE + '/masuk', safe=''), method='PUT')
tab = json.loads(urllib.request.urlopen(_req, timeout=20).read())
ws = create_connection(tab['webSocketDebuggerUrl'], timeout=90)
kirim(ws, 1, 'Page.enable'); kirim(ws, 2, 'Runtime.enable')
time.sleep(3)

# login (halaman /masuk kadang lambat — coba 2x)
for coba in range(3):
    h = nilai(ws, 10 + coba, """
    (function(){
      var e=document.querySelector('input[name=email]')||document.querySelector('input[type=email]');
      var p=document.querySelector('input[name=password]')||document.querySelector('input[type=password]');
      if(!e||!p) return 'BELUM SIAP';
      e.value='wulan@bikinaja.me'; p.value=%r; e.closest('form').submit();
      return 'SUBMIT';
    })()
    """ % PW)
    print('login coba', coba + 1, '→', h)
    if h == 'SUBMIT':
        break
    time.sleep(3)

time.sleep(6)
kirim(ws, 20, 'Page.navigate', {'url': f'{BASE}/naskah'})
time.sleep(6)

# ── tunggu daftar pembimbing muncul, lalu buka Log Revisi ────────────────
print('\n══ ISI HALAMAN DAFTAR NASKAH ══')
print(nilai(ws, 30, "document.body.innerText.slice(0,2200)"))

# klik tombol pembimbing / log
hasil = nilai(ws, 40, """
(async function(){
  var b=[...document.querySelectorAll('button,a')]
    .filter(x=>/pembimbing|Log Revisi/i.test(x.innerText||''));
  if(!b.length) return 'TOMBOL PEMBIMBING TIDAK DITEMUKAN';
  b[0].click();
  await new Promise(r=>setTimeout(r,3000));
  var t=document.body.innerText||'';
  var i=t.indexOf('Log Revisi');
  return i>=0 ? t.slice(Math.max(0,i-400), i+1400) : 'Log Revisi tidak muncul; tombol=['
        + b.map(x=>x.innerText.trim()).join(' | ')+']';
})()
""")
print('\n══ SETELAH KLIK TOMBOL PEMBIMBING ══')
print(hasil)

r = kirim(ws, 50, 'Page.captureScreenshot',
          {'format': 'png', 'captureBeyondViewport': True})
out = '/tmp/mhs_pembimbing.png'
open(out, 'wb').write(base64.b64decode(r['result']['data']))
print(f'\npotret: {out} · {os.path.getsize(out):,} byte')
ws.close()
print('PATH_POTRET=' + out)
