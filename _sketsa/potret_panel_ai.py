"""POTRET panel Asisten AI — TUNGGU editor selesai, lalu BUKA panel.

Perbedaan dari potret pertama: kita TUNGGU tulisan 'Menyiapkan editor'
hilang (maks 60 dtk), lalu klik tombol 'Asisten AI' supaya panel terbuka,
baru dipotret.
"""
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
    return r.get('result', {}).get('result', {}).get('value')


_r = subprocess.run(['docker', 'exec', 'eduai-app', 'python3', '-c',
    "import sys;sys.path.insert(0,'/app');"
    "from app.models import SessionLocal,User,FileBerkas;"
    "db=SessionLocal();u=db.query(User).filter(User.email=='wulan@bikinaja.me').first();"
    "fb=db.query(FileBerkas).filter(FileBerkas.user_id==u.id).first();"
    "print(fb.id)"], capture_output=True, text=True)
fid = int(_r.stdout.strip())
print('file_id =', fid)

_req = urllib.request.Request(
    CDP + '/json/new?' + urllib.parse.quote(BASE + '/masuk', safe=''), method='PUT')
tab = json.loads(urllib.request.urlopen(_req, timeout=20).read())
ws = create_connection(tab['webSocketDebuggerUrl'], timeout=90)
kirim(ws, 1, 'Page.enable'); kirim(ws, 2, 'Runtime.enable')
time.sleep(3)

print('login...')
print(nilai(ws, 3, """
(function(){
  var e=document.querySelector('input[name=email]')||document.querySelector('input[type=email]');
  var p=document.querySelector('input[name=password]')||document.querySelector('input[type=password]');
  if(!e||!p) return 'FORM TIDAK ADA';
  e.value='wulan@bikinaja.me'; p.value=%r; e.closest('form').submit();
  return 'SUBMIT';
})()
""" % PW))

time.sleep(6)
kirim(ws, 4, 'Page.navigate', {'url': f'{BASE}/edit/{fid}'})

# ── TUNGGU editor selesai dimuat ────────────────────────────────────────
print('menunggu editor selesai dimuat (maks 90 dtk)...')
siap = False
for i in range(30):
    time.sleep(3)
    t = nilai(ws, 100 + i, "document.body.innerText||''")
    if t and 'Menyiapkan editor' not in t:
        siap = True
        print(f'  ✅ editor siap setelah ±{(i+1)*3} dtk')
        break
    if i % 4 == 0:
        print(f'  ... masih memuat ({(i+1)*3} dtk)')
if not siap:
    print('  ⚠️ editor belum selesai 90 dtk — potret apa adanya')

# ── BUKA panel Asisten AI ───────────────────────────────────────────────
print('buka panel Asisten AI...')
hasil = nilai(ws, 200, """
(function(){
  var kandidat=[...document.querySelectorAll('button,a,div[role=button]')]
    .filter(b=>/Asisten AI/i.test(b.innerText||''));
  if(kandidat.length){ kandidat[0].click(); return 'DIKLIK: '+kandidat[0].innerText.trim().slice(0,40); }
  var p=document.querySelector('#panel-ai');
  if(p){ p.hidden=false; p.removeAttribute('hidden'); return 'PANEL DIBUKA PAKSA'; }
  return 'TOMBOL TIDAK DITEMUKAN';
})()
""")
print(' ', hasil)
time.sleep(4)

# ── info panel: apakah kotak komentar ada? ──────────────────────────────
print('\n══ ISI LAYAR SEKARANG ══')
print(nilai(ws, 300, "document.body.innerText.slice(0,1800)"))

# ── POTRET ──────────────────────────────────────────────────────────────
r = kirim(ws, 400, 'Page.captureScreenshot',
          {'format': 'png', 'captureBeyondViewport': True})
out = '/tmp/editor_ai_panel.png'
open(out, 'wb').write(base64.b64decode(r['result']['data']))
print(f'\npotret: {out} · {os.path.getsize(out):,} byte')
ws.close()
print('PATH_POTRET=' + out)
