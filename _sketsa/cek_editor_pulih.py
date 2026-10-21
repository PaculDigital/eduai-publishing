"""Cek editor /edit/78: modal galat TAMPIL atau TIDAK + potret. Versi ringan (tanpa wrapper net)."""
import base64
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import potret_cdp as P                                                   # noqa: E402

DASAR = 'https://eduai.bikinaja.id'
nama = os.environ['EDUAI_COOKIE_NAME']
nilai = os.environ['EDUAI_SESSION']
FID = os.environ.get('EDUAI_FID', '78')

P.bersihkan_tab()
tab, tid = P.tab_baru('about:blank')
try:
    tab.cmd('Page.enable')
    tab.cmd('Network.setCookie', {'name': nama, 'value': nilai,
                                  'url': DASAR, 'path': '/'})
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': 1500, 'height': 1200, 'deviceScaleFactor': 1,
             'mobile': False})
    tab.cmd('Page.navigate', {'url': DASAR + '/edit/' + FID})
    print('menunggu 45 dtk dokumen dimuat...')
    time.sleep(45)

    def js(e, t=90):
        r = tab.cmd('Runtime.evaluate', {'expression': e, 'returnByValue': True},
                    timeout=t)
        res = r.get('result', {})
        if res.get('exceptionDetails'):
            return 'LEMPAR ' + str(res['exceptionDetails'].get('text', ''))[:120]
        return res.get('result', {}).get('value')

    print('modal_galat  :', js("""(function(){
        var g = document.getElementById('galat');
        if (!g || g.hidden) return 'TIDAK-TAMPIL (bagus)';
        return (document.getElementById('galat-pesan')||{}).textContent || '';
    })()"""))
    print('kanvas_iframe:', js("document.querySelectorAll('iframe').length"))
    print('judul        :', js("document.title"))

    r = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=90)
    data = r.get('result', {}).get('data')
    if data:
        with open('/tmp/editor_oo3.png', 'wb') as f:
            f.write(base64.b64decode(data))
        print('png:', os.path.getsize('/tmp/editor_oo3.png'), 'byte')
finally:
    try:
        tab.tutup()
    except Exception:                                                    # noqa: BLE001
        pass
