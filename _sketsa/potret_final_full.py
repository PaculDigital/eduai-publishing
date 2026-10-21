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

#  ── GULUNG ke Log Revisi, lalu potret bagian itu saja ──
print('gulung:', n("""(() => {
  var e = document.getElementById('kb-log');
  if(!e) return 'ELEMEN HILANG';
  e.scrollIntoView({block:'center'});
  return 'top=' + Math.round(e.getBoundingClientRect().top) +
    ' tinggi=' + Math.round(e.getBoundingClientRect().height) +
    ' display=' + getComputedStyle(e).display;
})()"""))
time.sleep(2)
#  Ambil potret elemen Log Revisi langsung (bukan seluruh halaman).
res2 = t.tanya('Page.captureScreenshot', format='png')
d = res2.get('result', {}).get('data')
if d:
    p = f'{OUT}/16-log-ikon-tampak.png'
    open(p, 'wb').write(base64.b64decode(d))
    print(f'✅ {p} ({os.path.getsize(p)} byte)')
else:
    print('potret gagal:', json.dumps(res2)[:200])
