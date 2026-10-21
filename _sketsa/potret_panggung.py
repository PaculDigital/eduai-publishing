"""Panggil fungsi ASLI aplikasi (bukaBagikan→kbMuatDaftar→kbMuatLog) lalu potret.

KENAPA panggil fungsi, bukan klik: panel Bagikan adalah OVERLAY (.latar.buka),
klik biasa tidak membukanya di CDP. Memanggil fungsi asli = menguji kode ASLI.
"""
import base64, os, sys, subprocess, time, json
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
t.tanya('Emulation.setDeviceMetricsOverride', width=1300, height=1700,
        deviceScaleFactor=1, mobile=False)
t.tanya('Network.setCookie', name=nama, value=token, domain='eduai.bikinaja.id',
        path='/', secure=True, httpOnly=True)
t.tanya('Page.navigate', url='https://eduai.bikinaja.id/naskah')
time.sleep(10)


def n(e):
    res = t.tanya('Runtime.evaluate', expression=e, returnByValue=True,
                  awaitPromise=True)
    v = res.get('result', {}).get('result', {})
    return v.get('value') if 'value' in v else ('GALAT:' + str(v.get('description', ''))[:90])


print('buka panel + muat log:', n("""(async () => {
  bukaBagikan();
  await new Promise(function(r){setTimeout(r, 4000);});
  var el = document.getElementById('kb-log');
  return 'display=' + (el ? getComputedStyle(el).display : 'HILANG') +
    ' ikon=' + document.querySelectorAll('.kb-ik').length +
    ' baris=' + document.querySelectorAll('.kb-log-baris').length +
    ' aksi=' + document.querySelectorAll('.kb-aksi').length;
})()"""))
print('ringkasan :', str(n("document.getElementById('kb-log-angka')"
                          ".textContent.replace(/\\s+/g,' ').trim().slice(0,120)")))
print('lencana   :', str(n("[].slice.call(document.querySelectorAll('.kb-log-lencana'))"
                          ".map(function(x){return x.textContent.trim();}).join(' | ')")))
print('tooltip   :', str(n("[].slice.call(document.querySelectorAll('.kb-ik'))"
                          ".slice(0,3).map(function(x){return x.getAttribute('data-tip');})"
                          ".join(' | ')")))
print('href ikon :', str(n("[].slice.call(document.querySelectorAll('.kb-ik use'))"
                          ".slice(0,3).map(function(u){return u.getAttribute('href');})"
                          ".join(' | ')")))
t.tanya('Page.bringToFront')
time.sleep(2)
res = t.tanya('Page.captureScreenshot', format='png')
d = res.get('result', {}).get('data')
if d:
    p = f'{OUT}/15-log-ikon-jadi.png'
    open(p, 'wb').write(base64.b64decode(d))
    print(f'✅ {p} ({os.path.getsize(p)} byte)')
else:
    print('potret gagal:', json.dumps(res)[:200])

#  ── Log Revisi berada di dalam OVERLAY tertutup (tinggi=0). Untuk uji MATA,
#  pindahkan elemennya ke wadah terlihat, pakai CSS yang SAMA, data SAMA.
print('pindah & potret:', n("""(() => {
  var e = document.getElementById('kb-log');
  if(!e) return 'ELEMEN HILANG';
  //  tutup overlay, lalu tempelkan log ke body supaya benar-benar terlihat
  var l = document.getElementById('latar-bagikan');
  if (l) l.classList.remove('buka');
  var wadah = document.createElement('div');
  wadah.id = '__panggung';
  wadah.style.cssText = 'background:#F6F7F5;padding:20px;max-width:900px';
  document.body.insertBefore(wadah, document.body.firstChild);
  wadah.appendChild(e);
  e.style.display = 'block';
  e.style.marginTop = '0';
  var r = e.getBoundingClientRect();
  return 'tinggi=' + Math.round(r.height) + ' ikon=' +
    document.querySelectorAll('.kb-ik').length;
})()"""))
time.sleep(2)
res3 = t.tanya('Page.captureScreenshot', format='png')
d3 = res3.get('result', {}).get('data')
if d3:
    p3 = f'{OUT}/17-log-ikon-terlihat.png'
    open(p3, 'wb').write(base64.b64decode(d3))
    print(f'✅ {p3} ({os.path.getsize(p3)} byte)')
else:
    print('potret gagal:', json.dumps(res3)[:200])
