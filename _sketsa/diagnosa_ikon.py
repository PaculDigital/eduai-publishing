"""Diagnosa + POTRET: kenapa ikon .kb-ik = 0 padahal baris ada.

Langkah: buka /naskah → klik Bagikan → kbMuatLog() → panggil kbIkonSvg →
periksa isi .kb-log-baris → potret.
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
    return v.get('value') if 'value' in v else ('GALAT:' + str(v.get('description', ''))[:80])


#  klik Bagikan supaya panel + log dimuat
n("""(() => {var b=[].slice.call(document.querySelectorAll('button,a,div,span'))
  .filter(function(x){return /Bagikan ke Pembimbing/i.test(
    (x.textContent||'').trim())&&x.textContent.length<60;})[0];
  if(b) b.click(); return !!b;})()""")
time.sleep(6)
print('1 display kb-log :', n("(function(){var e=document.getElementById('kb-log');"
                             "return e?getComputedStyle(e).display:'HILANG';})()"))
print('2 ikon .kb-ik    :', n("document.querySelectorAll('.kb-ik').length"))
print('3 .kb-log-baris  :', n("document.querySelectorAll('.kb-log-baris').length"))
print('4 ada kb-aksi?   :', n("document.getElementById('kb-log-baris')"
                             ".innerHTML.indexOf('kb-aksi')"))
print('5 kbIkonSvg      :', n("typeof ikonSvg"))
print('6 ik-sparkles di dok:', n("document.documentElement.outerHTML.split('ik-sparkles').length - 1"))
print('7 potongan HTML  :', str(n("document.getElementById('kb-log-baris')"
                                ".innerHTML.slice(0,260)"))[:300])
t.tanya('Page.bringToFront')
time.sleep(2)
res = t.tanya('Page.captureScreenshot', format='png')
d = res.get('result', {}).get('data')
if d:
    p = f'{OUT}/14-log-ikon.png'
    open(p, 'wb').write(base64.b64decode(d))
    print(f'✅ {p} ({os.path.getsize(p)} byte)')
else:
    print('potret gagal:', json.dumps(res)[:200])
