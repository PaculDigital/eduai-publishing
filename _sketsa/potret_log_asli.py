"""Potret Log Revisi di halaman ASLI — buka panelnya dulu, lalu potret.

Cara: suntik cookie sesi, buka /naskah, cari & klik yang membuka Log Revisi,
lalu potret. Dipakai fungsi `Tab` dari potret_asli_sesi.
"""
import base64, hashlib, os, sys, time, json
sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_asli_sesi import Tab
import subprocess

OUT = '/opt/data/services/eduai-publishing/_potret/sketsa-ikon'
os.makedirs(OUT, exist_ok=True)

kode = ("from app.auth import buat_token\n"
        "from app.config import SESSION_COOKIE\n"
        "print(SESSION_COOKIE + '|' + buat_token(3))\n")
r = subprocess.run(['docker', 'exec', '-w', '/app', 'eduai-app', 'python3', '-c',
                    kode], capture_output=True, text=True, timeout=90)
nama_cookie, token = r.stdout.strip().split('|', 1)

t = Tab('about:blank')
t.tanya('Page.enable')
t.tanya('Emulation.setDeviceMetricsOverride', width=1250, height=1700,
        deviceScaleFactor=1, mobile=False)
t.tanya('Network.setCookie', name=nama_cookie, value=token,
        domain='eduai.bikinaja.id', path='/', secure=True, httpOnly=True)
t.tanya('Page.navigate', url='https://eduai.bikinaja.id/naskah')
time.sleep(9)


def nilai(expr):
    r2 = t.tanya('Runtime.evaluate', expression=expr, returnByValue=True,
                 awaitPromise=True)
    return r2.get('result', {}).get('result', {}).get('value')


print('url:', nilai('location.href'))
print('tombol mirip Log:', nilai("""(() => {
  var out=[];
  [].slice.call(document.querySelectorAll('button,a,[role=button],div,span'))
    .forEach(function(x){var t=(x.textContent||'').trim();
      if(/[Ll]og [Rr]evisi|[Rr]iwayat [Rr]evisi/i.test(t)&&t.length<70) out.push(t);});
  return out.slice(0,4).join(' | ') || '(tidak ada)';
})()"""))
print('klik:', nilai("""(() => {
  var x=[].slice.call(document.querySelectorAll('button,a,[role=button],div,span'))
    .filter(function(y){var t=(y.textContent||'').trim();
      return /[Ll]og [Rr]evisi|[Rr]iwayat [Rr]evisi/i.test(t)&&t.length<70;})[0];
  if(!x) return 'TIDAK KETEMU';
  x.click(); return 'diklik: '+(x.textContent||'').trim().slice(0,40);
})()"""))
time.sleep(5)
print('ikon .kb-ik   :', nilai("document.querySelectorAll('.kb-ik').length"))
print('lencana       :', nilai("""[].slice.call(document.querySelectorAll('.kb-log-lencana'))
  .map(function(x){return x.textContent.trim();}).join(' | ') || '(kosong)'"""))
print('tooltip       :', nilai("""[].slice.call(document.querySelectorAll('.kb-ik'))
  .map(function(x){return x.getAttribute('data-tip');}).slice(0,3).join(' | ') || '(kosong)'"""))
print('warna ikon    :', nilai("""(() => {var o={};
  [].slice.call(document.querySelectorAll('.kb-ik')).slice(0,3).forEach(function(x){
    o[getComputedStyle(x).color]=(o[getComputedStyle(x).color]||0)+1;});
  return JSON.stringify(o);})()"""))
print('href ikon     :', nilai("""[].slice.call(document.querySelectorAll('.kb-ik use'))
  .slice(0,3).map(function(u){return u.getAttribute('href');}).join(' | ') || '(kosong)'"""))
t.tanya('Page.bringToFront')
time.sleep(2)
res = t.tanya('Page.captureScreenshot', format='png', captureBeyondViewport=True)
d = res.get('result', {}).get('data')
if d:
    p = f'{OUT}/11-log-revisi-asli.png'
    open(p, 'wb').write(base64.b64decode(d))
    print(f'✅ {p} ({os.path.getsize(p)} byte)')
else:
    print('potret gagal:', json.dumps(res)[:250])
