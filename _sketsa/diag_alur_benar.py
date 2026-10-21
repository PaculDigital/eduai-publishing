"""Diagnosa 30Sep26 — ALUR BENAR: tiap tahap tutup kartu dengan BATAL
(bukan sembunyikan manual) lalu pilih ulang. Buktikan body jalur 1/2/3
+ respons server. TANPA klik 'Terapkan' (kuota tak disentuh).
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
              m.jawab = t.slice(0,300); }).catch(function(){}); })
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


def baru(tab, sebelum):
    return js(tab,
              f"JSON.stringify((window.__logF||[]).slice({sebelum}).filter("
              "function(x){return x.url.indexOf('/v1/proses')<0;}).map("
              "function(x){return {u:x.url.split('/').pop(), b:x.body, "
              "j:x.jawab};}))", 0.4)


def kartu(tab):
    return js(tab, """(function(){
      var w = document.getElementById('pai-wadah-izin');
      var b = document.getElementById('pai-jalan');
      return JSON.stringify({kartu: w && !w.hidden,
        teks: (b.textContent||'').slice(0,30),
        isi: w ? w.innerText.replace(/\\s+/g,' ').slice(0,220) : null}); })()""",
              0.3)


def batal(tab):
    """Klik tombol Batal di kartu lingkup (aktifkan lagi tombol)."""
    return js(tab, """(function(){
      var w = document.getElementById('pai-wadah-izin');
      if (!w || w.hidden) return 'KARTU-TIDAK-ADA';
      var bs = w.querySelectorAll('button');
      for (var i=0;i<bs.length;i++){
        if (bs[i].textContent.indexOf('Batal') === 0) { bs[i].click();
          return 'batal diklik'; } }
      return 'TOMBOL-BATAL-TIDAK-ADA'; })()""", 1)


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
        js(tab, "document.getElementById('tombol-ai').click();", 5)
        js(tab, """(function(){
            var k = document.getElementById('pai-kotak');
            k.value = 'Perdalam kajian pustaka di bagian ini ya.';
            k.dispatchEvent(new Event('input', {bubbles:true}));
            document.getElementById('pai-tambah').click(); })()""", 1.5)

        #  ── JALUR 3: kepala BAB III ──
        js(tab, """(function(){var r=document.querySelector(
            'input[name="pai-bab"][value="BAB III"]'); r.click();})()""", 1.5)
        n = js(tab, "(window.__logF||[]).length", 0.2)
        js(tab, "document.getElementById('pai-jalan').click();", 5)
        print('  [JALUR 3]', baru(tab, n))
        print('  [kartu3]', kartu(tab))
        print('  batal:', batal(tab))
        print('  [sesudah batal]', kartu(tab))

        #  ── JALUR 2: centang 3.1 (+ cek apakah centangan MENEMPEL) ──
        print('  centang 3.1:', js(tab, """(function(){
            var c = document.querySelector(
              'input[name="pai-sub"][value="3.1"]');
            if (!c) return 'TIDAK-ADA'; c.click();
            return 'checked=' + c.checked; })()""", 1.5))
        print('  centang 3.2 (uji ganda):', js(tab, """(function(){
            var c = document.querySelector(
              'input[name="pai-sub"][value="3.2"]');
            if (!c) return 'TIDAK-ADA'; c.click();
            return 'checked=' + c.checked; })()""", 1.5))
        n = js(tab, "(window.__logF||[]).length", 0.2)
        js(tab, "document.getElementById('pai-jalan').click();", 5)
        print('  [JALUR 2]', baru(tab, n))
        print('  [kartu2]', kartu(tab))
        print('  batal:', batal(tab))

        #  ── JALUR 1: paragraf pembuka ──
        print('  klik pembuka:', js(tab, """(function(){
            var p = document.querySelector(
              'input[name="pai-pembuka"][value="BAB III"]');
            if (!p) return 'TIDAK-ADA'; p.click();
            return 'checked=' + p.checked; })()""", 1.5))
        n = js(tab, "(window.__logF||[]).length", 0.2)
        js(tab, "document.getElementById('pai-jalan').click();", 5)
        print('  [JALUR 1]', baru(tab, n))
        print('  [kartu1]', kartu(tab))
        print('  batal:', batal(tab))
        print('  [selesai] tombol:', kartu(tab))
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
