"""UJI KLIK NYATA tombol "EduAi bantu isi" (13Okt26).

Yang dibuktikan: klik tombol di BROWSER SUNGGUHAN → kata kunci muncul di
kotak (chip) → pesan tampil. Ini yang tidak bisa dibuktikan uji unit.

Alat resmi potret_cdp.py. Login lewat Network.setCookie SEBELUM navigasi.
"""
import base64
import http.client
import json
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
print('  ✅ login OK', flush=True)

PC.bersihkan_tab()
tab, tid = PC.tab_baru('about:blank')
try:
    tab.cmd('Page.enable')
    tab.cmd('Network.enable')
    nama, nilai = ck.split('=', 1)
    tab.cmd('Network.setCookie', {'name': nama, 'value': nilai,
                                  'domain': ip, 'path': '/', 'httpOnly': True})
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': 1120, 'height': 1500, 'deviceScaleFactor': 1,
             'mobile': False})
    tab.cmd('Page.navigate', {'url': BASE + '/referensi'})
    time.sleep(7)

    #  ── 1. Isi judul ke kotak (kalau ada kolomnya) lalu KLIK tombol ──
    pra = tab.cmd('Runtime.evaluate', {'expression': (
        "JSON.stringify({kolom:document.querySelectorAll('input,textarea').length,"
        " tombol:!!document.getElementById('btn-bantu'),"
        " pesan:(document.getElementById('pesan')||{}).innerText||''})"),
        'returnByValue': True}, timeout=30)
    print('  keadaan awal:', pra.get('result', {}).get('result', {}).get('value'),
          flush=True)

    #  Klik tombol bantu
    klik = tab.cmd('Runtime.evaluate', {'expression': (
        "var b=document.getElementById('btn-bantu'); if(!b) 'TIDAK ADA'; "
        "else { b.click(); 'DIKLIK'; }"), 'returnByValue': True}, timeout=30)
    print('  klik:', klik.get('result', {}).get('result', {}).get('value'),
          flush=True)
    time.sleep(9)          # beri waktu AI + jaringan

    hasil = tab.cmd('Runtime.evaluate', {'expression': (
        "JSON.stringify({"
        " pesan:(document.getElementById('pesan')||{}).innerText||'',"
        " kelas_pesan:((document.getElementById('pesan')||{}).className)||'',"
        " nilai_kolom:(document.getElementById('kk-ai')||{}).value||'',"
        " jumlah_chip:document.querySelectorAll('.chip-konsep,.konsep-chip').length,"
        " teks_chip:Array.from(document.querySelectorAll('.chip-konsep,.konsep-chip'))"
        "            .map(function(c){return c.innerText.trim();}).slice(0,8)"
        "})"), 'returnByValue': True}, timeout=40)
    val = hasil.get('result', {}).get('result', {}).get('value')
    print('  hasil klik:', val, flush=True)

    g = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=60)
    raw = base64.b64decode(g['result']['data'])
    open('/opt/data/ref_ai_4_klik.png', 'wb').write(raw)
    print(f'  ✅ /opt/data/ref_ai_4_klik.png — {len(raw)} byte', flush=True)
finally:
    try:
        import urllib.request as U
        U.urlopen(f'{PC.CDP}/json/close/{tid}', timeout=5).read()
    except Exception:                                                 # noqa: BLE001
        pass
    tab.tutup()
