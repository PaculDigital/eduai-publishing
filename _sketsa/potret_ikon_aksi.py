"""POTRET ikon aksi + lencana "Revisi Dilewati" di halaman naskah mahasiswa."""
import json, sys, time, base64, os, urllib.request
from websocket import create_connection

BASE = 'https://eduai.bikinaja.id'
CDP = 'http://127.0.0.1:9341'
EMAIL, SANDI = os.environ['EDUAI_UJI_EMAIL'], os.environ['EDUAI_UJI_SANDI']
OUT = '/opt/data/services/eduai-publishing/_potret/sketsa-ikon'
os.makedirs(OUT, exist_ok=True)


def cdp_baru():
    r = urllib.request.Request(CDP + '/json/new?about:blank', method='PUT')
    for _ in range(25):
        try:
            return json.loads(urllib.request.urlopen(r, timeout=8).read())
        except Exception:
            time.sleep(1)
    raise SystemExit('CDP tidak menjawab')


tab = cdp_baru()['webSocketDebuggerUrl']
ws = create_connection(tab, timeout=90)
_id = [0]


def cmd(method, **par):
    _id[0] += 1
    ws.send(json.dumps({'id': _id[0], 'method': method, 'params': par}))
    while True:
        d = json.loads(ws.recv())
        if d.get('id') == _id[0]:
            return d.get('result', {})


def js(expr, tunggu=0.0):
    r = cmd('Runtime.evaluate', expression=expr, awaitPromise=True,
            returnByValue=True)
    if tunggu:
        time.sleep(tunggu)
    return r.get('result', {}).get('value')


cmd('Page.enable')
cmd('Runtime.enable')
js(f"location.href='{BASE}/masuk'")
time.sleep(3)
js(f"""(() => {{
  var f=document.querySelector('form');
  var e=document.querySelector('input[type=email],input[name=email]');
  var p=document.querySelector('input[type=password],input[name=sandi]');
  if(!f||!e||!p) return 'FORM TIDAK KETEMU';
  e.value={EMAIL!r}; p.value={SANDI!r}; f.submit();
  return 'kirim login';
}})()""")
time.sleep(5)
print('url setelah login:', js('location.href'))
