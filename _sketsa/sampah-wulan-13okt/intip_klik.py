"""INTIP KONSOL browser saat klik tombol — jangan tebak sebabnya (13Okt26).

Pelajaran lama: `[object Object]` = diagnosa buta → pakai JSON.stringify.
Di sini: matikan konsol-log + tangkap error + tangkap jawaban jaringan.
"""
import base64
import http.client
import re
import subprocess
import sys
import time
import urllib.parse

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
import potret_cdp as PC                                                # noqa: E402

out = subprocess.run(['getent', 'hosts', 'eduai-app'],
                     capture_output=True, text=True).stdout.split()
ip = out[0]
BASE = f'http://{ip}:8000'

c = http.client.HTTPConnection(ip, 8000, timeout=25)
body = urllib.parse.urlencode({'email': 'potret-ref@eduai.test',
                               'password': 'UjiPotret2026!'})
c.request('POST', '/masuk', body,
          {'Content-Type': 'application/x-www-form-urlencoded'})
r = c.getresponse()
r.read()
ck = re.search(r'(eduai_session=[^;]+)', r.getheader('set-cookie', '')).group(1)
print('login OK', flush=True)

PC.bersihkan_tab()
tab, tid = PC.tab_baru('about:blank')
try:
    tab.cmd('Page.enable')
    tab.cmd('Network.enable')
    tab.cmd('Runtime.enable')
    nama, nilai = ck.split('=', 1)
    tab.cmd('Network.setCookie', {'name': nama, 'value': nilai,
                                  'domain': ip, 'path': '/', 'httpOnly': True})
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': 1120, 'height': 1400, 'deviceScaleFactor': 1,
             'mobile': False})
    tab.cmd('Page.navigate', {'url': BASE + '/referensi'})
    time.sleep(7)

    #  ── Cek 1: apakah fungsi bantuIsi ADA di halaman ini? ──
    ada = tab.cmd('Runtime.evaluate', {'expression': (
        "JSON.stringify({"
        " bantuIsi:typeof bantuIsi,"
        " cariAI:typeof cariAI,"
        " tombol:!!document.getElementById('btn-bantu'),"
        " onclick:(document.getElementById('btn-bantu')||{}).getAttribute"
        "         ?document.getElementById('btn-bantu').getAttribute('onclick'):''"
        "})"), 'returnByValue': True}, timeout=30)
    print('  fungsi:', ada.get('result', {}).get('result', {}).get('value'),
          flush=True)

    #  ── Cek 2: isi judul lalu klik, TANGKAP error ──
    tab.cmd('Runtime.evaluate', {'expression': (
        "window.__err=[]; window.addEventListener('error',function(e){"
        " window.__err.push(String(e.message)+' @'+(e.filename||'')+':'+e.lineno);"
        "}); var _f=window.fetch; window.__net=[]; window.fetch=function(u,o){"
        " window.__net.push(String(u)); return _f.apply(this,arguments); };"
        " var i=document.getElementById('kk-ai');"
        " i.value='Pengaruh Keaslian Streamer terhadap Pembelian Impulsif';"
        " i.dispatchEvent(new Event('input',{bubbles:true})); 'SIAP'"),
        'returnByValue': True}, timeout=30)
    time.sleep(1)
    tab.cmd('Runtime.evaluate', {'expression':
                                 "document.getElementById('btn-bantu').click();",
                                 'returnByValue': True}, timeout=30)
    time.sleep(10)

    hasil = tab.cmd('Runtime.evaluate', {'expression': (
        "JSON.stringify({err:window.__err||[], net:window.__net||[],"
        " pesan:(document.getElementById('pesan')||{}).innerText||'',"
        " nilai:(document.getElementById('kk-ai')||{}).value||''})"),
        'returnByValue': True}, timeout=30)
    print('  HASIL:', hasil.get('result', {}).get('result', {}).get('value'),
          flush=True)

    g = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=60)
    raw = base64.b64decode(g['result']['data'])
    open('/opt/data/ref_ai_6_intip.png', 'wb').write(raw)
    print(f'  ✅ /opt/data/ref_ai_6_intip.png — {len(raw)} byte', flush=True)
finally:
    try:
        import urllib.request as U
        U.urlopen(f'{PC.CDP}/json/close/{tid}', timeout=5).read()
    except Exception:                                                 # noqa: BLE001
        pass
    tab.tutup()
