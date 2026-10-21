"""Diagnosa 30Sep26 — setelah T1 (langkahHitung jalan sekali), klik mati.
Probe: disabled? event change fires? exception? Tanpa klik 'Terapkan'.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import potret_cdp as P                                                   # noqa: E402

DASAR = 'https://eduai.bikinaja.id'
URL = DASAR + '/edit/78'

JEBEKAN = """(function(){
  window.__err = [];
  window.addEventListener('error', function(e){
    window.__err.push(String(e.message) + ' @' + (e.filename||'').split('/').pop()
                      + ':' + e.lineno); }, true);
  window.addEventListener('unhandledrejection', function(e){
    window.__err.push('REJECT ' + String(e.reason).slice(0,200)); });
  window.__logF = [];
  var _f = window.fetch;
  window.fetch = function(u, opt){
    var m = {url: String(u), body: opt && opt.body ? String(opt.body) : null};
    window.__logF.push(m);
    var p = _f.apply(this, arguments);
    try { p.then(function(r){ m.status = r.status;
            return r.clone().text().then(function(t){
              m.jawab = t.slice(0,200); }).catch(function(){}); })
          .catch(function(){}); } catch(e){}
    return p;
  };
  window.__ubah = 0;
  document.addEventListener('change', function(){
    window.__ubah++; }, true);
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


def probe(tab):
    return js(tab, """(function(){
      var b = document.getElementById('pai-jalan');
      var c = document.querySelector('input[name="pai-sub"][value="3.1"]');
      var r = document.querySelector('input[name="pai-bab"]:checked');
      var p = document.querySelector('input[name="pai-pembuka"]');
      return JSON.stringify({
        jalan: b ? {disabled: b.disabled, teks: (b.textContent||'').slice(0,40)}
                 : 'TIDAK-ADA',
        sub31: c ? {checked: c.checked, disabled: c.disabled,
                    onchange: typeof c.onchange} : 'TIDAK-ADA',
        radio: r ? {v: r.value, disabled: r.disabled,
                    onchange: typeof r.onchange} : 'TIDAK-ADA',
        pembuka: p ? {checked: p.checked, disabled: p.disabled,
                      onchange: typeof p.onchange} : 'TIDAK-ADA',
        nInput: document.querySelectorAll(
          '#pai-bab-daftar input').length,
        err: window.__err || 'TANPA-JEBEKAN',
        nFetch: (window.__logF || []).length,
        nUbah: window.__ubah
      }); })()""", 0.4)


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
        print('  jebakan:', js(tab, JEBEKAN, 0.5))
        js(tab, "document.getElementById('tombol-ai').click();", 5)
        print('  [AWAL]', probe(tab))

        js(tab, """(function(){var r=document.querySelector(
            'input[name="pai-bab"][value="BAB III"]'); r.click();})()""", 1.5)
        js(tab, """(function(){
            var k = document.getElementById('pai-kotak');
            k.value = 'Perdalam kajian pustaka di bagian ini ya.';
            k.dispatchEvent(new Event('input', {bubbles:true}));
            document.getElementById('pai-tambah').click(); })()""", 1.5)
        print('  klik pai-jalan:', js(tab,
            "var b=document.getElementById('pai-jalan'); b.click();"
            "'klik, disabled=' + b.disabled", 5))
        print('  [SETELAH T1]', probe(tab))

        print('  klik 3.1:', js(tab, """(function(){
            var c = document.querySelector(
              'input[name="pai-sub"][value="3.1"]');
            if (!c) return 'TIDAK-ADA';
            c.click();
            return 'checked=' + c.checked; })()""", 2))
        print('  [SESUDAH KLIK 3.1]', probe(tab))
        print('  fetch terakhir:', js(tab,
            "JSON.stringify((window.__logF||[]).slice(-2))", 0.3))
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
