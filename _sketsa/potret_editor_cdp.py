"""POTRET layar editor EduAi lewat CDP — login dulu, baru buka /edit/<fid>."""
import json, sys, time, base64, os
import urllib.request
from websocket import create_connection   # type: ignore

#  ⚠️ Chrome di HOST: 127.0.0.1:8100 TIDAK bisa (000, loopback container).
#     Pakai DOMAIN: https://eduai.bikinaja.id (terbukti 200).
BASE = 'https://eduai.bikinaja.id'
PW = sys.argv[1]
CDP = 'http://127.0.0.1:9333'


def kirim(ws, mid, method, params=None):
    ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
    while True:
        d = json.loads(ws.recv())
        if d.get('id') == mid:
            return d


# 1. tab baru
_req = urllib.request.Request(
    CDP + '/json/new?' + urllib.parse.quote(BASE + '/masuk', safe=''),
    method='PUT')
tab = json.loads(urllib.request.urlopen(_req, timeout=20).read())
ws = create_connection(tab['webSocketDebuggerUrl'], timeout=60)
kirim(ws, 1, 'Page.enable')
kirim(ws, 2, 'Runtime.enable')
time.sleep(2)

# 2. isi form login + submit (cara user sungguhan)
js = """
(function(){
  var e=document.querySelector('input[name=email]')||document.querySelector('input[type=email]');
  var p=document.querySelector('input[name=password]')||document.querySelector('input[type=password]');
  if(!e||!p) return 'FORM TIDAK ADA';
  e.value=%r; p.value=%r;
  var f=e.closest('form');
  if(f){ f.submit(); return 'SUBMIT'; }
  return 'FORM KOSONG';
})()
""" % ('wulan@bikinaja.me', PW)
r = kirim(ws, 3, 'Runtime.evaluate', {'expression': js, 'returnByValue': True})
print('login:', r.get('result', {}).get('result', {}).get('value'))
time.sleep(4)

# 3. sekarang buka editor
import subprocess
_out = subprocess.run(['docker', 'exec', 'eduai-app', 'python3', '-c',
    "import sys;sys.path.insert(0,'/app');"
    "from app.models import SessionLocal,User,FileBerkas;"
    "db=SessionLocal();u=db.query(User).filter(User.email=='wulan@bikinaja.me').first();"
    "fb=db.query(FileBerkas).filter(FileBerkas.user_id==u.id).first();"
    "print(fb.id, fb.nama)"], capture_output=True, text=True)
fid = int(_out.stdout.split()[0])
print('dari container:', _out.stdout.strip())
class fb: id = fid
kirim(ws, 4, 'Page.navigate', {'url': f'{BASE}/edit/{fb.id}'})
time.sleep(8)

# 4. gulir ke bagian Asisten AI
kirim(ws, 5, 'Runtime.evaluate', {'expression': """
(function(){
  var t=document.body.innerText||'';
  var i=t.indexOf('Asisten AI');
  var el=document.querySelector('#panel-ai')||document.querySelector('[id*=ai]');
  var target = el || document.querySelector('button');
  if(target) target.scrollIntoView({block:'center'});
  return JSON.stringify({ada_asisten: i>=0, tinggi: document.body.scrollHeight});
})()
""", 'returnByValue': True})
time.sleep(2)

# 5. potret
r = kirim(ws, 6, 'Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': True})
out = f'/tmp/editor_eduai.png'
open(out, 'wb').write(base64.b64decode(r['result']['data']))
print('potret:', out, os.path.getsize(out), 'byte')

# 6. ambil daftar teks yang terlihat
r = kirim(ws, 7, 'Runtime.evaluate', {'expression':
    "document.body.innerText.slice(0,2500)", 'returnByValue': True})
print('\n══ TEKS TERLIHAT DI LAYAR ══')
print(r.get('result', {}).get('result', {}).get('value', ''))
ws.close()
print('\nPATH_POTRET=' + out)
