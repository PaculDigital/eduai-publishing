"""Potret + bukti klik tombol "pakai juga di bab…" (13Okt26).

CARA BENAR (setelah 3 kali gagal, semua tercatat):
  1. Socket ke :9333 = CDP BROWSER-level ⇒ Page.* MENGGANTUNG.
     ⇒ WAJIB ambil `webSocketDebuggerUrl` per-TAB dari /json/list.
  2. Cookie tab lama = user lain ⇒ WAJIB pasang cookie user uji SENDIRI.
  3. Urutan: buat tab → Page.enable → setDeviceMetrics → setCookie →
     Page.navigate → tunggu (JANGAN navigate 2×).
"""
import base64
import json
import re
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from ws_mentah import WS                                    # noqa: E402

FILE_ID = 105
BAB = 'BAB III'
USER_UJI = 9
MARKA = 'eduai.bikinaja.id'
PORT = 9333


def buat_tab(url='about:blank'):
    """Buat tab BARU lewat HTTP endpoint CDP."""
    try:
        with urllib.request.urlopen(
                f'http://127.0.0.1:{PORT}/json/new?{url}', timeout=20) as f:
            return json.load(f)
    except Exception:                                              # noqa: BLE001
        req = urllib.request.Request(f'http://127.0.0.1:{PORT}/json/new?{url}',
                                     method='PUT')
        with urllib.request.urlopen(req, timeout=20) as f:
            return json.load(f)


#  ── token user uji ──
kode = ("from app.auth import buat_token\n"
        "from app.config import SESSION_COOKIE\n"
        f"print(SESSION_COOKIE + '|' + buat_token({USER_UJI}))\n")
r = subprocess.run(['docker', 'exec', '-w', '/app', 'eduai-app', 'python3',
                    '-c', kode], capture_output=True, text=True, timeout=90)
if r.returncode != 0:
    sys.exit('token gagal: ' + r.stderr[-200:])
nama_cookie, token = r.stdout.strip().split('|', 1)
print(f'cookie {nama_cookie} untuk user {USER_UJI}')

#  ── tab BARU ──
tab = buat_tab('about:blank')
ws_url = tab['webSocketDebuggerUrl']
print('tab baru:', tab['id'][:12])

c = WS(ws_url)
c.cmd('Page.enable')
c.cmd('Network.enable')
c.cmd('Emulation.setDeviceMetricsOverride', width=390, height=1500,
      deviceScaleFactor=1, mobile=True)
hasil = c.cmd('Network.setCookie', name=nama_cookie, value=token,
              domain=MARKA, path='/', secure=True, httpOnly=True)
print('cookie disuntik:', hasil.get('success'))
c.cmd('Page.navigate', url=f'https://{MARKA}/referensi')
time.sleep(9)

#  ── pilih naskah 105 + BAB III → muat ──
skrip = f'''(async () => {{
  const sel = document.querySelector('#naskah-ai');
  if (sel) {{ const o=[...sel.options].find(x=>String(x.value)==='{FILE_ID}');
             if(o){{ sel.value=o.value; sel.dispatchEvent(new Event('change')); }} }}
  const bab = document.querySelector('#bab-ai');
  if (bab) {{ bab.value='{BAB}'; bab.dispatchEvent(new Event('change')); }}
  await new Promise(r=>setTimeout(r,1000));
  if (typeof muat==='function') {{ await muat('{BAB}'); }}
  await new Promise(r=>setTimeout(r,1800));
  const b=[...document.querySelectorAll('button')]
    .filter(x=>x.textContent.indexOf('pakai juga di bab')>=0);
  return JSON.stringify({{
    url: location.pathname, naskah: sel?sel.value:null, bab: bab?bab.value:null,
    kartu: document.querySelectorAll('.art').length, tombolPakai: b.length,
    teks: b.length?b[0].textContent.trim():null,
    kosong: !!document.querySelector('.kosong')}});
}})()'''
h = c.cmd('Runtime.evaluate', expression=skrip, awaitPromise=True,
          returnByValue=True)
val = h.get('result', {}).get('value')
print('HASIL:', val)

#  ── potret area kartu artikel ──
kotak = c.cmd('Runtime.evaluate', returnByValue=True, expression="""(() => {
  const b=[...document.querySelectorAll('button')]
    .filter(x=>x.textContent.indexOf('pakai juga di bab')>=0);
  if(!b.length) return null;
  const r=b[0].getBoundingClientRect();
  return JSON.stringify({y: Math.max(0, Math.round(r.top + window.scrollY) - 260),
                         akhir: Math.round(r.bottom + window.scrollY) + 120});
})()""")
kt = kotak.get('result', {}).get('value')
y0, y1 = (json.loads(kt)['y'], json.loads(kt)['akhir']) if kt else (900, 2100)
print(f'area potret: y={y0}..{y1}')

data = c.cmd('Page.captureScreenshot', format='png', captureBeyondViewport=True,
             clip={'x': 0, 'y': y0, 'width': 390, 'height': max(600, y1 - y0),
                   'scale': 1})['data']
raw = base64.b64decode(data)
open('/opt/data/pb_tombol.png', 'wb').write(raw)
print(f'✅ /opt/data/pb_tombol.png — {len(raw)} byte')
