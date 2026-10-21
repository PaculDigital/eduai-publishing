"""Potret editor /edit/78 SETELAH render penuh (progress bar hilang + teks ada)."""
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
                return None
            return res.get('result', {}).get('value')
        except Exception:                                                # noqa: BLE001
            return 'TIMEOUT'

    # tunggu sampai: tidak ada teks 'Memuat dokumen' / 'Menyiapkan' DAN ada paragraf
    t0 = time.time()
    siap = False
    for i in range(30):                       # s/d 300 dtk
        time.sleep(10)
        keadaan = js("""(function(){
            var t = document.body.innerText || '';
            var memuat = /Memuat dokumen|Menyiapkan editor/i.test(t);
            var fr = document.querySelectorAll('iframe');
            var par = 0, kar = 0;
            for (var i=0;i<fr.length;i++){
              try { var w = fr[i].contentWindow;
                if (w && w.editor && w.editor.private_GetLogicDocument){
                  var ld = w.editor.private_GetLogicDocument();
                  if (ld){ par = ld.GetAllParagraphs ? ld.GetAllParagraphs().length : 0;
                           kar = ld.GetAllText ? ld.GetAllText().length : 0; }
                }
              } catch(e){}
            }
            return JSON.stringify({memuat: memuat, par: par, kar: kar});
        })()""", t=25)
        print(f'  t={int(time.time()-t0):3d}s -> {keadaan}')
        if isinstance(keadaan, str) and keadaan.startswith('{'):
            import json
            try:
                d = json.loads(keadaan)
            except Exception:                                            # noqa: BLE001
                continue
            if (not d.get('memuat')) and d.get('par', 0) > 0:
                siap = True
                break

    print('SIAP:', siap)
    time.sleep(3)
    r = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=90)
    data = r.get('result', {}).get('data')
    if data:
        with open('/tmp/editor_penuh.png', 'wb') as f:
            f.write(base64.b64decode(data))
        print('png:', os.path.getsize('/tmp/editor_penuh.png'), 'byte')
finally:
    try:
        tab.tutup()
    except Exception:                                                    # noqa: BLE001
        pass
