"""Potret ikon aksi di HALAMAN EDITOR (/edit/9) — tempat Log Revisi hidup.

Pelajaran 24Sep26: Log Revisi TIDAK ada di /naskah (daftar berkas) — ada di
EDITOR. Wulan mula-mula salah alamat lalu menyalahkan kode. Baca dulu di
mana fitur hidup, JANGAN menebak.
"""
import base64, os, sys, time, json, subprocess
sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_asli_sesi import Tab

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
t.tanya('Emulation.setDeviceMetricsOverride', width=1400, height=1900,
        deviceScaleFactor=1, mobile=False)
t.tanya('Network.setCookie', name=nama_cookie, value=token,
        domain='eduai.bikinaja.id', path='/', secure=True, httpOnly=True)
t.tanya('Page.navigate', url='https://eduai.bikinaja.id/edit/9')
time.sleep(16)          # editor OnlyOffice butuh waktu


def nilai(e):
    r2 = t.tanya('Runtime.evaluate', expression=e, returnByValue=True,
                 awaitPromise=True)
    return r2.get('result', {}).get('result', {}).get('value')


print('url        :', nilai('location.href'))
print('judul      :', nilai('document.title'))
print('ikon .kb-ik:', nilai("document.querySelectorAll('.kb-ik').length"))
print('panel AI   :', nilai("!!document.querySelector('.pai, #panel-ai, [class*=asisten]')"))
print('teks Log   :', nilai("""(() => {
  var el=[].slice.call(document.querySelectorAll('*'))
    .filter(function(x){return /Log Revisi/i.test(x.textContent||'')&&
      x.children.length<3;})[0];
  return el ? el.textContent.trim().slice(0,80) : '(tidak ketemu)';
})()"""))

#  Buka panel Asisten AI kalau ada tombolnya
print('buka panel :', nilai("""(() => {
  var b=[].slice.call(document.querySelectorAll('button,a,div,span'))
    .filter(function(x){var t=(x.textContent||'').trim();
      return /Asisten AI/i.test(t)&&t.length<40;})[0];
  if(!b) return 'TOMBOL TIDAK KETEMU';
  b.click(); return 'diklik';
})()"""))
time.sleep(4)
print('ikon setelah buka:', nilai("document.querySelectorAll('.kb-ik').length"))
t.tanya('Page.bringToFront')
time.sleep(2)
res = t.tanya('Page.captureScreenshot', format='png', captureBeyondViewport=True)
d = res.get('result', {}).get('data')
if d:
    p = f'{OUT}/12-editor-log-revisi.png'
    open(p, 'wb').write(base64.b64decode(d))
    print(f'✅ {p} ({os.path.getsize(p)} byte)')
else:
    print('potret gagal:', json.dumps(res)[:250])
