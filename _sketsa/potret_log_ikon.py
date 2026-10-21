"""Potret Log Revisi + ikon aksi di /naskah, bimbingan 65 (Prof. Uji Bab).

KUNCI yang Wulan salah pahami sebelumnya: Log Revisi hanya tampil kalau
dropdown "Naskah yang dibagikan" menunjuk berkas yang MEMANG punya bimbingan.
"""
import base64, os, sys, time, json, subprocess
sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_asli_sesi import Tab

OUT = '/opt/data/services/eduai-publishing/_potret/sketsa-ikon'

kode = ("from app.auth import buat_token\nfrom app.config import SESSION_COOKIE\n"
        "print(SESSION_COOKIE + '|' + buat_token(3))\n")
r = subprocess.run(['docker', 'exec', '-w', '/app', 'eduai-app', 'python3', '-c',
                    kode], capture_output=True, text=True, timeout=90)
nama, token = r.stdout.strip().split('|', 1)

t = Tab('about:blank')
t.tanya('Page.enable')
t.tanya('Emulation.setDeviceMetricsOverride', width=1300, height=1900,
        deviceScaleFactor=1, mobile=False)
t.tanya('Network.setCookie', name=nama, value=token, domain='eduai.bikinaja.id',
        path='/', secure=True, httpOnly=True)
t.tanya('Page.navigate', url='https://eduai.bikinaja.id/naskah')
time.sleep(9)


def nilai(e):
    res = t.tanya('Runtime.evaluate', expression=e, returnByValue=True,
                  awaitPromise=True)
    return res.get('result', {}).get('result', {}).get('value')


print('klik Bagikan:', nilai("""(() => {
  var b=[].slice.call(document.querySelectorAll('button,a,div,span'))
    .filter(function(x){var t=(x.textContent||'').trim();
      return /Bagikan ke Pembimbing/i.test(t)&&t.length<60;})[0];
  if(!b) return 'TIDAK KETEMU'; b.click(); return 'diklik';})()"""))
time.sleep(6)
print('pilihan naskah:', nilai("""(() => {var s=document.querySelectorAll('select');
  if(!s.length) return '(tidak ada select)';
  return [].slice.call(s[0].options).map(function(o){return o.value+':'+o.textContent.trim().slice(0,28);}).join(' | ');})()"""))
print('pilih file 9  :', nilai("""(() => {var s=document.querySelectorAll('select');
  if(!s.length) return 'tidak ada';
  var o=[].slice.call(s[0].options).filter(function(x){return /9|Goras|TESIS/i.test(x.textContent+x.value);})[0];
  if(!o) return 'opsi tidak ada';
  s[0].value=o.value;
  s[0].dispatchEvent(new Event('change',{bubbles:true}));
  return 'dipilih: '+o.textContent.trim().slice(0,30);})()"""))
time.sleep(6)
print('kb-log display:', nilai("""(() => {var e=document.getElementById('kb-log');
  return e?getComputedStyle(e).display:'ELEMEN TIDAK ADA';})()"""))
print('ikon .kb-ik   :', nilai("document.querySelectorAll('.kb-ik').length"))
print('angka ringkas :', nilai("""(() => {var e=document.getElementById('kb-log-angka');
  return e?(e.textContent||'').replace(/\\s+/g,' ').trim().slice(0,150):'(kosong)';})()"""))
print('lencana       :', nilai("""[].slice.call(document.querySelectorAll('.kb-log-lencana'))
  .map(function(x){return x.textContent.trim();}).join(' | ')||'(kosong)'"""))
print('tooltip       :', nilai("""[].slice.call(document.querySelectorAll('.kb-ik'))
  .slice(0,3).map(function(x){return x.getAttribute('data-tip');}).join(' | ')||'(kosong)'"""))
print('href ikon     :', nilai("""[].slice.call(document.querySelectorAll('.kb-ik use'))
  .slice(0,3).map(function(u){return u.getAttribute('href');}).join(' | ')||'(kosong)'"""))
t.tanya('Page.bringToFront')
time.sleep(2)
res = t.tanya('Page.captureScreenshot', format='png', captureBeyondViewport=True)
d = res.get('result', {}).get('data')
if d:
    p = f'{OUT}/13-log-revisi-ikon.png'
    open(p, 'wb').write(base64.b64decode(d))
    print(f'✅ {p} ({os.path.getsize(p)} byte)')
else:
    print('potret gagal:', json.dumps(res)[:200])
