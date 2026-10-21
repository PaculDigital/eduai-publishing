"""UJI KLIK LENGKAP: isi JUDUL → klik "EduAi bantu isi" → chip muncul.

Ini pembuktian penuh: mesin AI memetakan judul → kata kunci (13Okt26).
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
            {'width': 1120, 'height': 1600, 'deviceScaleFactor': 1,
             'mobile': False})
    tab.cmd('Page.navigate', {'url': BASE + '/referensi'})
    time.sleep(7)

    #  ── 1. Isi JUDUL di kolom kata kunci bagian ① ──
    isi = tab.cmd('Runtime.evaluate', {'expression': (
        "var i=document.getElementById('kk-ai');"
        "if(!i) JSON.stringify({ok:false,sebab:'kolom kk-ai tidak ada'});"
        "else { i.value='Pengaruh Keaslian Streamer dan Interaksi Parasosial "
        "terhadap Pembelian Impulsif pada Live Streaming Commerce';"
        " i.dispatchEvent(new Event('input',{bubbles:true}));"
        " JSON.stringify({ok:true, nilai:i.value}); }"),
        'returnByValue': True}, timeout=30)
    print('  isi judul:', isi.get('result', {}).get('result', {}).get('value'),
          flush=True)
    time.sleep(1)

    #  ── 2. Klik tombol bantu ──
    klik = tab.cmd('Runtime.evaluate', {'expression': (
        "var b=document.getElementById('btn-bantu'); b.click(); 'DIKLIK';"),
        'returnByValue': True}, timeout=30)
    print('  klik:', klik.get('result', {}).get('result', {}).get('value'),
          flush=True)

    #  ── 3. Tunggu & pantau hasil (sampai 40 dtk) ──
    akhir = None
    for detik in range(1, 21):
        time.sleep(2)
        h = tab.cmd('Runtime.evaluate', {'expression': (
            "JSON.stringify({"
            " pesan:(document.getElementById('pesan')||{}).innerText||'',"
            " nilai:(document.getElementById('kk-ai')||{}).value||''"
            "})"), 'returnByValue': True}, timeout=30)
        val = h.get('result', {}).get('result', {}).get('value') or '{}'
        akhir = val
        if '"pesan":"' in val.replace(' ', '') and 'Konsep utama' not in val:
            pass
        print(f'    t={detik*2}s: {val[:160]}', flush=True)
        #  berhenti kalau pesan sudah muncul
        if val.count('\\u') < 2 and ('kata kunci' in val.lower()
                                     or 'judul' in val.lower()
                                     or 'memetakan' in val.lower()):
            break

    g = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=60)
    raw = base64.b64decode(g['result']['data'])
    open('/opt/data/ref_ai_5_hasil.png', 'wb').write(raw)
    print(f'  ✅ /opt/data/ref_ai_5_hasil.png — {len(raw)} byte', flush=True)
    print('  AKHIR:', akhir, flush=True)
finally:
    try:
        import urllib.request as U
        U.urlopen(f'{PC.CDP}/json/close/{tid}', timeout=5).read()
    except Exception:                                                 # noqa: BLE001
        pass
    tab.tutup()
