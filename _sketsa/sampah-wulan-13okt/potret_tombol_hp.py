"""Potret ZOOM bagian ① Pilihan EduAi (tombol "EduAi bantu isi") — 13Okt26.

Alat resmi `potret_cdp.py`. Login disuntik lewat Network.setCookie.
Lebar dikecilkan (900px) supaya tombol tampak BESAR & jelas untuk mata.
"""
import base64
import http.client
import os
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
print('base:', BASE)

c = http.client.HTTPConnection(ip, 8000, timeout=25)
body = urllib.parse.urlencode({'email': 'potret-ref@eduai.test',
                               'password': 'UjiPotret2026!'})
c.request('POST', '/masuk', body,
          {'Content-Type': 'application/x-www-form-urlencoded'})
r = c.getresponse()
r.read()
ck = re.search(r'(eduai_session=[^;]+)', r.getheader('set-cookie', '')).group(1)
print('login OK')

PC.bersihkan_tab()
tab, tid = PC.tab_baru('about:blank')
try:
    tab.cmd('Page.enable')
    tab.cmd('Network.enable')
    nama, nilai = ck.split('=', 1)
    tab.cmd('Network.setCookie', {'name': nama, 'value': nilai,
                                  'domain': ip, 'path': '/', 'httpOnly': True})
    #  Viewport HP (390) → tampilan sama seperti yang dilihat mahasiswa.
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': 430, 'height': 900, 'deviceScaleFactor': 2,
             'mobile': True})
    tab.cmd('Page.navigate', {'url': BASE + '/referensi'})
    time.sleep(7)
    #  Gulir tepat ke tombol, lalu potret.
    info = tab.cmd('Runtime.evaluate', {'expression': (
        "var b=document.getElementById('btn-bantu');"
        "if(b){b.scrollIntoView({block:'center'});}"
        "JSON.stringify({ada:!!b,teks:b?b.innerText:'',"
        "y:b?Math.round(b.getBoundingClientRect().top):-1,"
        "w:b?Math.round(b.getBoundingClientRect().width):0})"),
        'returnByValue': True}, timeout=30)
    print('tombol:', info.get('result', {}).get('result', {}).get('value'))
    time.sleep(2)
    g = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=60)
    raw = base64.b64decode(g['result']['data'])
    keluar = '/opt/data/ref_ai_3_hp.png'
    open(keluar, 'wb').write(raw)
    print(f'✅ {keluar} — {len(raw)} byte')
finally:
    try:
        import urllib.request as U
        U.urlopen(f'{PC.CDP}/json/close/{tid}', timeout=5).read()
    except Exception:                                                 # noqa: BLE001
        pass
    tab.tutup()
