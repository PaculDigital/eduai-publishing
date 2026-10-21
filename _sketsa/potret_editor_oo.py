"""Potret /edit/78 — buktikan editor OnlyOffice TAMPIL (galat "Editor tidak bisa dimuat" hilang).

PAKAI alat yang SUDAH TERBUKTI: potret_cdp (socket mentah CDP :9333) + kunci
sesi via Network.setCookie (pola uji_fix_3jalur.py).
"""
import base64
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import potret_cdp as P                                                   # noqa: E402

DASAR = 'https://eduai.bikinaja.id'

nama = os.environ.get('EDUAI_COOKIE_NAME')
nilai = os.environ.get('EDUAI_SESSION')
if not nama or not nilai:
    print('EDUAI_COOKIE_NAME / EDUAI_SESSION belum diisi')
    sys.exit(2)

P.bersihkan_tab()
tab, tid = P.tab_baru('about:blank')
try:
    tab.cmd('Page.enable')
    tab.cmd('Network.enable')
    tab.cmd('Network.setCookie', {'name': nama, 'value': nilai,
                                  'url': DASAR, 'path': '/'})
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': 1500, 'height': 1400, 'deviceScaleFactor': 1,
             'mobile': False})
    tab.cmd('Page.navigate', {'url': DASAR + '/edit/78'})
    time.sleep(14)          # OnlyOffice perlu waktu muat api.js + dokumen

    def js(ekspresi):
        r = tab.cmd('Runtime.evaluate', {'expression': ekspresi,
                                         'returnByValue': True}, timeout=60)
        res = r.get('result', {})
        if res.get('exceptionDetails'):
            return 'LEMPAR: ' + str(res['exceptionDetails'].get('text', ''))[:200]
        return res.get('result', {}).get('value')

    galat = js("""(function(){
        var b = document.body.innerText || '';
        return b.indexOf('Editor tidak bisa dimuat') >= 0;
    })()""")
    err = js("""(function(){ var e = (window.__err||[]);
        return e.length ? e.slice(0,5) : 'TIDAK-ADA'; })()""")
    ifr = js("""(function(){
        var f = document.querySelector('iframe');
        if (!f) return 'TANPA-IFRAME';
        var d = null;
        try { d = f.contentDocument; } catch (e) {}
        return {src: (f.src||'').slice(0,90),
                teks: d ? (d.body.innerText||'').slice(0,240) : '(cross-origin)',
                panjang: d ? (d.body.innerText||'').length : -1};
    })()""")
    r = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=60)
    data = r.get('result', {}).get('data')
    keluar = '/tmp/editor_oo.png'
    if data:
        with open(keluar, 'wb') as f:
            f.write(base64.b64decode(data))
    print('galat_editor:', galat)
    print('error_jendela:', err)
    print('iframe:', ifr)
    print('png:', keluar,
          os.path.getsize(keluar) if os.path.exists(keluar) else 0, 'byte')
finally:
    try:
        tab.tutup()
    except Exception:                                                    # noqa: BLE001
        pass
