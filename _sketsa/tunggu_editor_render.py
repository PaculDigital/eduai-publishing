"""Tunggu ADAPTIF editor sampai dokumen TER-RENDER (private_GetLogicDocument ada isinya).
Bukan tebak jeda: pantau tiap 10 dtk sampai 240 dtk. Simpan potret akhir."""
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

    def js(e, t=30):
        try:
            r = tab.cmd('Runtime.evaluate',
                        {'expression': e, 'returnByValue': True}, timeout=t)
            res = r.get('result', {})
            if res.get('exceptionDetails'):
                return 'LEMPAR ' + str(res['exceptionDetails'].get('text', ''))[:100]
            return res.get('result', {}).get('value')
        except Exception as ex:                                          # noqa: BLE001
            return 'TIMEOUT ' + str(ex)[:60]

    # Cek tiap 10 dtk -> apakah iframe editor sudah punya LogicDocument berisi
    t0 = time.time()
    akhir = 'BELUM'
    for putaran in range(24):                     # 24 x 10 = 240 dtk maks
        time.sleep(10)
        dtk = int(time.time() - t0)
        # cari frame OO di dalam iframe (same-origin lewat /oo/aset)
        hasil = js("""(function(){
            var fr = document.querySelectorAll('iframe');
            for (var i=0;i<fr.length;i++){
                try {
                    var w = fr[i].contentWindow;
                    if (w && w.editor && typeof w.editor.private_GetLogicDocument === 'function'){
                        var ld = w.editor.private_GetLogicDocument();
                        if (ld) {
                            var txt = '';
                            try { txt = ld.GetAllText ? ld.GetAllText() : ''; } catch(e){}
                            var par = 0;
                            try { par = ld.GetAllParagraphs ? ld.GetAllParagraphs().length : 0; } catch(e){}
                            return 'RENDER kar=' + (txt?txt.length:0) + ' par=' + par;
                        }
                    }
                } catch(e){}
            }
            var g = document.getElementById('galat');
            var gal = (!g || g.hidden) ? '' : ((document.getElementById('galat-pesan')||{}).textContent||'').slice(0,80);
            return 'MENUNGGU' + (gal ? ' | GALAT: ' + gal : '');
        })()""", t=25)
        print(f'  t={dtk:3d}s -> {hasil}')
        if isinstance(hasil, str) and hasil.startswith('RENDER'):
            akhir = hasil
            break
        if isinstance(hasil, str) and 'GALAT' in hasil:
            akhir = 'GALAT: ' + hasil
            break

    print('HASIL:', akhir)
    r = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=90)
    data = r.get('result', {}).get('data')
    if data:
        with open('/tmp/editor_oo4.png', 'wb') as f:
            f.write(base64.b64decode(data))
        print('png:', os.path.getsize('/tmp/editor_oo4.png'), 'byte')
finally:
    try:
        tab.tutup()
    except Exception:                                                    # noqa: BLE001
        pass
