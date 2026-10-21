"""Diagnosa 30Sep26 — kenapa pilihan jalur 1/2 tak terkirim ke /v1/hitung?

Rekam SEMUA fetch (URL + body) + keadaan DOM setelah tiap klik.
TANPA klik "Terapkan" (jangan sampai revisi/kuota tersentuh).
/ & /v1/hitung tidak memotong kuota (hitung = tanya harga saja).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import potret_cdp as P                                                   # noqa: E402

DASAR = 'https://eduai.bikinaja.id'
URL = DASAR + '/edit/78'

SPY = """(function(){
  if (window.__logF) return 'sudah-ada';
  window.__logF = [];
  var _f = window.fetch;
  window.fetch = function(u, opt){
    var masuk = {url: String(u), body: opt && opt.body ? String(opt.body) : null};
    window.__logF.push(masuk);
    var p = _f.apply(this, arguments);
    try {
      p.then(function(r){
        var sal = r.clone();
        masuk.status = r.status;
        return sal.text().then(function(t){
          masuk.jawab = t.slice(0, 300);
        }).catch(function(){});
      }).catch(function(){});
    } catch(e){}
    return p;
  };
  return 'terpasang';
})()"""


def js(tab, ekspresi, tunggu=1.0):
    r = tab.cmd('Runtime.evaluate', {'expression': ekspresi,
                                     'returnByValue': True,
                                     'awaitPromise': False}, timeout=60)
    res = r.get('result', {})
    if res.get('exceptionDetails'):
        return 'LEMPAR: ' + str(res['exceptionDetails'].get('text', ''))[:200]
    time.sleep(tunggu)
    return res.get('result', {}).get('value')


def dom(tab):
    return js(tab, """(function(){
      var r = document.querySelector('input[name="pai-bab"]:checked');
      var c = document.querySelector('input[name="pai-sub"][value="3.1"]');
      var p = document.querySelector('input[name="pai-pembuka"]:checked');
      var w = document.getElementById('pai-wadah-izin');
      return JSON.stringify({
        radio: r ? r.value : null,
        cek31: c ? c.checked : 'TIDAK-ADA',
        pembuka: p ? p.value : null,
        nSub: document.querySelectorAll('input[name="pai-sub"]').length,
        kartu: w ? {hidden: w.hidden, isi: w.innerText.replace(/\\s+/g,' ').slice(0,120)}
                 : 'TIDAK-ADA'
      }); })()""", 0.4)


def log(tab):
    return js(tab, "JSON.stringify(window.__logF || [])", 0.3)


def main():
    nama = os.environ.get('EDUAI_COOKIE_NAME')
    nilai = os.environ.get('EDUAI_SESSION')
    if not nama or not nilai:
        print('EDUAI_COOKIE_NAME / EDUAI_SESSION belum diisi')
        return 2
    P.bersihkan_tab()
    tab, tid = P.tab_baru('about:blank')
    try:
        tab.cmd('Page.enable')
        tab.cmd('Network.enable')
        tab.cmd('Network.setCookie', {'name': nama, 'value': nilai,
                'url': DASAR, 'path': '/'})
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': 1400, 'height': 1400, 'deviceScaleFactor': 1,
                 'mobile': False})
        tab.cmd('Page.navigate', {'url': URL})
        time.sleep(10)
        print('  spy:', js(tab, SPY, 0.5))
        print('  buka panel:', js(tab, """(function(){
            var t = document.getElementById('tombol-ai');
            if (!t) return 'TIDAK-ADA'; t.click(); return 'diklik'; })()""", 5))
        print('  [SETELAH BUKA]', dom(tab))
        print('  log setelah buka:', log(tab))

        #  1. klik kepala BAB III
        print('  klik kepala:', js(tab, """(function(){
            var r = document.querySelector(
              'input[name="pai-bab"][value="BAB III"]');
            if (!r) return 'TIDAK-ADA'; r.click(); return 'diklik'; })()""", 2))
        print('  [KEPALA]', dom(tab))
        #  2. centang 3.1
        print('  centang 3.1:', js(tab, """(function(){
            var c = document.querySelector(
              'input[name="pai-sub"][value="3.1"]');
            if (!c) return 'TIDAK-ADA'; c.click();
            return 'diklik, sesudah=' + c.checked; })()""", 2))
        print('  [CENTANG 3.1]', dom(tab))
        #  3. klik pembuka
        print('  klik pembuka:', js(tab, """(function(){
            var p = document.querySelector(
              'input[name="pai-pembuka"][value="BAB III"]');
            if (!p) return 'TIDAK-ADA'; p.click();
            return 'diklik, sesudah=' + p.checked; })()""", 2))
        print('  [PEMBUKA]', dom(tab))
        print('  log SEMUA fetch:', log(tab))
    finally:
        try:
            import urllib.request
            urllib.request.urlopen(f'{P.CDP}/json/close/{tid}', timeout=5).read()
        except Exception:                                                # noqa: BLE001
            pass
        tab.tutup()
    return 0


if __name__ == '__main__':
    sys.exit(main())
