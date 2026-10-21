"""Buka /edit/78 sambil memantau: siapa memanggil /oo/unduh, berapa status, dan isi modal galat."""
import base64
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import potret_cdp as P                                                   # noqa: E402

DASAR = 'https://eduai.bikinaja.id'
nama = os.environ['EDUAI_COOKIE_NAME']
nilai = os.environ['EDUAI_SESSION']

P.bersihkan_tab()
tab, tid = P.tab_baru('about:blank')
try:
    tab.cmd('Page.enable')
    tab.cmd('Network.enable')
    tab.cmd('Network.enable')
    # pantau SEMUA request yang mengandung unduh (dari sisi browser)
    tab.cmd('Runtime.evaluate', {'expression': """
        window.__net = [];
        var of = window.fetch, oo = XMLHttpRequest.prototype.open;
        window.fetch = function(u){ window.__net.push('F '+String(u).slice(0,120));
            return of.apply(this, arguments); };
        XMLHttpRequest.prototype.open = function(m, u){
            window.__net.push('X '+String(u).slice(0,120));
            return oo.apply(this, arguments); };
        'pasang';""", 'returnByValue': True})
    tab.cmd('Network.setCookie', {'name': nama, 'value': nilai,
                                  'url': DASAR, 'path': '/'})
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': 1500, 'height': 1400, 'deviceScaleFactor': 1,
             'mobile': False})
    tab.cmd('Page.navigate', {'url': DASAR + '/edit/78'})
    time.sleep(15)

    def js(e):
        r = tab.cmd('Runtime.evaluate', {'expression': e, 'returnByValue': True},
                    timeout=60)
        res = r.get('result', {})
        if res.get('exceptionDetails'):
            return 'LEMPAR ' + str(res['exceptionDetails'].get('text', ''))[:150]
        return res.get('result', {}).get('value')

    print('modal_galat:', js("""(function(){
        var g = document.getElementById('galat');
        if (!g || g.hidden) return 'TIDAK-TAMPIL';
        return (document.getElementById('galat-pesan')||{}).textContent || '';
    })()"""))
    print('info_unduh:', js("""(function(){
        var a = (window.__net||[]).filter(function(x){
            return x.indexOf('unduh') >= 0; });
        return a.length ? a.slice(0,5) : 'TANPA-PEMANGGILAN-UNDUH';
    })()"""))
    r = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=60)
    data = r.get('result', {}).get('data')
    if data:
        with open('/tmp/editor_oo2.png', 'wb') as f:
            f.write(base64.b64decode(data))
        print('png:', os.path.getsize('/tmp/editor_oo2.png'))
finally:
    try:
        tab.tutup()
    except Exception:                                                    # noqa: BLE001
        pass
