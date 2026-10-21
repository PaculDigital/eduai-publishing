"""Uji TEKAN: buka /edit/78 bersih, tunggu render, lalu TEKAN Simpan,
lalu periksa (a) modal galat tampil? (b) callback simpan 200? (c) potret."""
import base64
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import potret_cdp as P                                                   # noqa: E402

DASAR = 'https://eduai.bikinaja.id'
nama = os.environ['EDUAI_COOKIE_NAME']
nilai = os.environ['EDUAI_SESSION']
FID = os.environ.get('EDUAI_FID', '78')

tab, tid = P.tab_baru('about:blank')
try:
    tab.cmd('Page.enable')
    tab.cmd('Network.setCookie', {'name': nama, 'value': nilai,
                                  'url': DASAR, 'path': '/'})
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': 1500, 'height': 1100, 'deviceScaleFactor': 1,
             'mobile': False})
    tab.cmd('Page.navigate', {'url': DASAR + '/edit/' + FID})

    def js(e, t=25):
        try:
            r = tab.cmd('Runtime.evaluate',
                        {'expression': e, 'returnByValue': True}, timeout=t)
            res = r.get('result', {})
            if res.get('exceptionDetails'):
                return None
            return res.get('result', {}).get('value')
        except Exception:                                                # noqa: BLE001
            return 'TIMEOUT'

    # tunggu siap (paragraf ada) sampai 200 dtk
    siap = False
    for i in range(20):
        time.sleep(10)
        st = js("""(function(){
          var fr=document.querySelectorAll('iframe'), par=0;
          for (var i=0;i<fr.length;i++){ try{ var w=fr[i].contentWindow;
            if (w&&w.editor&&w.editor.private_GetLogicDocument){
              var d=w.editor.private_GetLogicDocument();
              if(d) par = d.GetAllParagraphs? d.GetAllParagraphs().length:0; } }catch(e){} }
          return par; })()""")
        print(f'  t={i*10+10:3d}s par={st}')
        if isinstance(st, int) and st > 0:
            siap = True
            break
    print('SIAP:', siap)

    # (a) modal galat TAMPIL?
    galat = js("""(function(){
        var t=document.body.innerText||'';
        var ada = /kesalahan saat bekerja dengan dokumen|Unduhan gagal|errorCode/i.test(t);
        return JSON.stringify({ada_modal_galat: ada});
    })()""")
    print('  modal:', galat)

    # (b) TEKAN tombol Simpan
    klik = js("""(function(){
        var b=[...document.querySelectorAll('button,a')]
          .find(x=>/Simpan/i.test(x.textContent||''));
        if(!b) return 'TOMBOl-TIDAK-ADA';
        b.click(); return 'DIKLIK'; })()""")
    print('  tombol Simpan:', klik)
    time.sleep(12)

    # (c) modal galat setelah simpan?
    galat2 = js("""(function(){
        var t=document.body.innerText||'';
        return JSON.stringify({
          modal_galat: /kesalahan saat bekerja dengan dokumen|Unduhan gagal|errorCode/i.test(t),
          ada_peringatan: /Peringatan/i.test(t)});})()""")
    print('  setelah simpan:', galat2)

    r = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=90)
    data = r.get('result', {}).get('data')
    if data:
        open('/tmp/editor_simpan.png', 'wb').write(base64.b64decode(data))
        print('  png:', os.path.getsize('/tmp/editor_simpan.png'), 'byte')
finally:
    try:
        tab.tutup()
    except Exception:                                                    # noqa: BLE001
        pass
