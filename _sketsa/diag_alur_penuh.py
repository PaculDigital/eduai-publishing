"""Diagnosa 30Sep26 — ALUR PENUH: kepala → tambah komentar → jalan →
centang 3.1 → jalan → pembuka → jalan. Spy SEMUA fetch (menumpuk).
TANPA klik "Terapkan" (kuota/berkas tak disentuh; /v1/hitung = tanya harga).
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
    var m = {url: String(u), body: opt && opt.body ? String(opt.body) : null};
    window.__logF.push(m);
    var p = _f.apply(this, arguments);
    try { p.then(function(r){ m.status = r.status;
            return r.clone().text().then(function(t){
              m.jawab = t.slice(0, 260); }).catch(function(){}); })
          .catch(function(){}); } catch(e){}
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
      return JSON.stringify({radio: r ? r.value : null,
        cek31: c ? c.checked : 'TIDAK-ADA',
        pembuka: p ? p.value : null}); })()""", 0.3)


def tahan(log, sebelum):
    """B hanya fetch BARU sejakindeks `sebelum`."""
    return js(log['tab'],
              f"JSON.stringify((window.__logF||[]).slice({sebelum}).filter("
              "function(x){return x.url.indexOf('/v1/proses')<0;}))", 0.4)


def main():
    nama = os.environ.get('EDUAI_COOKIE_NAME')
    nilai = os.environ.get('EDUAI_SESSION')
    if not nama or not nilai:
        print('EDUAI_COOKIE_NAME / EDUAI_SESSION belum diisi')
        return 2
    P.bersihkan_tab()
    tab, tid = P.tab_baru('about:blank')
    log = {'tab': tab}
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
        n = js(tab, "(window.__logF||[]).length", 0.3)
        print('  jumlah fetch dasar:', n)

        #  TAHAP 1 — kepala BAB III (jalur 3)
        js(tab, """(function(){var r=document.querySelector(
            'input[name="pai-bab"][value="BAB III"]'); r.click();})()""", 1.5)
        js(tab, """(function(){
            var k = document.getElementById('pai-kotak');
            k.value = 'Perdalam kajian pustaka di bagian ini ya.';
            k.dispatchEvent(new Event('input', {bubbles:true}));
            document.getElementById('pai-tambah').click(); })()""", 1.5)
        print('  [T1 dom]', dom(tab))
        n1 = js(tab, "(window.__logF||[]).length", 0.2)
        js(tab, "document.getElementById('pai-jalan').click();", 5)
        print('  [T1 fetch baru]', tahan(log, n1))
        print('  [T1 dom sesudah]', dom(tab))

        #  TAHAP 2 — centang 3.1 (jalur 2)
        print('  centang 3.1:', js(tab, """(function(){
            var c = document.querySelector(
              'input[name="pai-sub"][value="3.1"]');
            if (!c) return 'TIDAK-ADA'; c.click();
            return 'diklik, sesudah=' + c.checked; })()""", 1.5))
        print('  [T2 dom]', dom(tab))
        n2 = js(tab, "(window.__logF||[]).length", 0.2)
        js(tab, "document.getElementById('pai-jalan').click();", 5)
        print('  [T2 fetch baru]', tahan(log, n2))
        print('  [T2 dom sesudah]', dom(tab))

        #  TAHAP 3 — pembuka (jalur 1)
        print('  klik pembuka:', js(tab, """(function(){
            var p = document.querySelector(
              'input[name="pai-pembuka"][value="BAB III"]');
            if (!p) return 'TIDAK-ADA'; p.click();
            return 'diklik, sesudah=' + p.checked; })()""", 1.5))
        print('  [T3 dom]', dom(tab))
        n3 = js(tab, "(window.__logF||[]).length", 0.2)
        js(tab, "document.getElementById('pai-jalan').click();", 5)
        print('  [T3 fetch baru]', tahan(log, n3))
        print('  [T3 dom sesudah]', dom(tab))
        print('  TOTAL fetch:', js(tab, "(window.__logF||[]).length", 0.3))
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
