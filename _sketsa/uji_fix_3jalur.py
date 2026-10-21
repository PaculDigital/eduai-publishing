"""Uji FIX centang 3 jalur (30Sep2026) — asersi LULUS/GAGAL, exit≠0 kalau gagal.

Yang diuji:
  F1 kepala BAB III      → radio tercentang + body bab + server 3 Token
  F2 Batal               → kartu tutup + tombol aktif lagi
  F3 centang 3.1         → MENEMPEL (checked=true)
  F4 centang 3.2         → MENUMPUK (dua-duanya tercentang) + babs keduanya
  F5 server jalur 2      → 2 Token (harga_flat per sub-bab)
  F6 ganti pilihan saat kartu tampil → kartu TERTUTUP sendiri + tombol aktif
  F7 pembuka             → checked=true, sub & radio kepala bersih,
                           body lingkup='pembuka' + server 1 Token
  F8 balik ke kepala     → radio checked, sub bersih, server 3 Token
  F9 nol exception JS    (jebakan window error)

TANPA klik 'Terapkan' — kuota tidak disentuh.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import potret_cdp as P                                                   # noqa: E402

DASAR = 'https://eduai.bikinaja.id'
URL = DASAR + '/edit/78'

hasil = []


def cek(nama, kondisi, bukti=''):
    hasil.append((nama, bool(kondisi), bukti))
    print(('  ✅ LULUS ' if kondisi else '  ❌ GAGAL ') + nama +
          ((' — ' + str(bukti)[:220]) if bukti else ''))


SPY = """(function(){
  if (window.__err) return 'sudah-ada';
  window.__err = [];
  window.addEventListener('error', function(e){
    window.__err.push(String(e.message)+' @'+e.lineno); }, true);
  window.addEventListener('unhandledrejection', function(e){
    window.__err.push('REJECT '+String(e.reason).slice(0,160)); });
  window.__logF = [];
  var _f = window.fetch;
  window.fetch = function(u, opt){
    var m = {url: String(u), body: opt && opt.body ? String(opt.body) : null};
    window.__logF.push(m);
    var p = _f.apply(this, arguments);
    try { p.then(function(r){ m.status = r.status;
            return r.clone().text().then(function(t){
              m.jawab = t.slice(0,400); }).catch(function(){}); })
          .catch(function(){}); } catch(e){}
    return p;
  };
  return 'terpasang';
})()"""


def potret_tab(tab, keluar):
    import base64                                                        # noqa: E402
    r = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=60)
    data = r.get('result', {}).get('data')
    if not data:
        print('  ❌ gagal potret')
        return None
    with open(keluar, 'wb') as f:
        f.write(base64.b64decode(data))
    print(f'  📸 {keluar} — {os.path.getsize(keluar)} byte')
    return keluar


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
      var sub = [].filter.call(
        document.querySelectorAll('input[name="pai-sub"]'),
        function (x) { return x.checked; })
        .map(function (x) { return x.value; });
      var p = document.querySelector('input[name="pai-pembuka"]:checked');
      var b = document.getElementById('pai-jalan');
      var w = document.getElementById('pai-wadah-izin');
      return JSON.stringify({radio: r ? r.value : null, sub: sub,
        pembuka: p ? p.value : null,
        tombolAktif: b ? !b.disabled : null,
        teks: b ? (b.textContent||'').slice(0,24) : null,
        kartu: w ? !w.hidden : null}); })()""", 0.4)


def hitung_terakhir(tab, sebelum):
    return js(tab, """(function(){
      var a = (window.__logF||[]).slice(%d).filter(function(x){
        return x.url.indexOf('/v1/hitung') >= 0; });
      if (!a.length) return null;
      var m = a[a.length-1];
      try { var j = JSON.parse(m.jawab);
        return {b: m.body, rev: j.revisi_dibutuhkan, pesan: j.pesan,
                flat: j.harga_flat}; } catch(e){ return {b:m.body,
                err:String(m.jawab).slice(0,120)}; } })()""" % sebelum, 0.4)


def jumlah_fetch(tab):
    return js(tab, "(window.__logF||[]).length", 0.2)


def klik_jalan(tab):
    js(tab, "document.getElementById('pai-jalan').click();", 5)


def batal(tab):
    return js(tab, """(function(){
      var w = document.getElementById('pai-wadah-izin');
      if (!w || w.hidden) return 'KARTU-TIDAK-ADA';
      var bs = w.querySelectorAll('button');
      for (var i=0;i<bs.length;i++){
        if (bs[i].textContent.indexOf('Batal') === 0) { bs[i].click();
          return 'ok'; } }
      return 'TAK-ADA'; })()""", 1)


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
        js(tab, SPY, 0.5)
        js(tab, "document.getElementById('tombol-ai').click();", 5)
        js(tab, """(function(){
            var k = document.getElementById('pai-kotak');
            k.value = 'Perdalam kajian pustaka di bagian ini ya.';
            k.dispatchEvent(new Event('input', {bubbles:true}));
            document.getElementById('pai-tambah').click(); })()""", 1.5)

        #  ── F1: kepala BAB III ──
        js(tab, """(function(){document.querySelector(
            'input[name="pai-bab"][value="BAB III"]').click();})()""", 1.5)
        d = dom(tab)
        cek('F1a radio kepala BAB III tercentang',
            '"radio":"BAB III"' in d, d)
        n = jumlah_fetch(tab)
        klik_jalan(tab)
        h = hitung_terakhir(tab, n)
        cek('F1b body jalur 3 + server 3 Token',
            h and h.get('rev') == 3 and 'bab' in (h.get('b') or ''), h)
        cek('F1c kartu lingkup tampil',
            '"kartu":true' in dom(tab), dom(tab))

        #  ── F2: Batal → tombol aktif ──
        cek('F2a Batal ditemukan', batal(tab) == 'ok')
        d = dom(tab)
        cek('F2b kartu tutup + tombol aktif lagi',
            '"kartu":false' in d and '"tombolAktif":true' in d
            and 'Revisi dengan AI' in d, d)

        #  ── F3: centang 3.1 MENEMPEL ──
        js(tab, """(function(){document.querySelector(
            'input[name="pai-sub"][value="3.1"]').click();})()""", 1.5)
        d = dom(tab)
        cek('F3 centang 3.1 MENEMPEL', '"sub":["3.1"]' in d, d)

        #  ── F4: centang 3.2 → MENUMPUK ──
        js(tab, """(function(){document.querySelector(
            'input[name="pai-sub"][value="3.2"]').click();})()""", 1.5)
        d = dom(tab)
        cek('F4 centang 3.2 MENUMPUK (3.1+3.2)',
            '"sub":["3.1","3.2"]' in d, d)

        #  ── F5: kirim → babs dua-duanya + 2 Token ──
        n = jumlah_fetch(tab)
        klik_jalan(tab)
        h = hitung_terakhir(tab, n)
        b = (h or {}).get('b') or ''
        cek('F5 body jalur 2 = babs 3.1+3.2 · server 2 Token',
            h and h.get('rev') == 2 and '"3.1"' in b and '"3.2"' in b, h)

        #  ── F6: ganti pilihan TANPA Batal → kartu tutup sendiri ──
        d = dom(tab)
        cek('F6a kartu tampil sebelum ganti pilihan',
            '"kartu":true' in d, d)
        js(tab, """(function(){document.querySelector(
            'input[name="pai-pembuka"][value="BAB III"]').click();})()""",
           1.5)
        d = dom(tab)
        cek('F6b kartu TERTUTUP sendiri + tombol aktif (lepasKartu)',
            '"kartu":false' in d and '"tombolAktif":true' in d
            and 'Revisi dengan AI' in d, d)

        #  ── F7: pembuka ──
        cek('F7a centang pembuka MENEMPEL + sub & radio bersih',
            '"pembuka":"BAB III"' in d and '"sub":[]' in d
            and '"radio":null' in d, d)
        n = jumlah_fetch(tab)
        klik_jalan(tab)
        h = hitung_terakhir(tab, n)
        cek('F7b body lingkup=pembuka + server 1 Token',
            h and h.get('rev') == 1 and 'pembuka' in (h.get('b') or ''), h)

        #  ── F8: balik ke kepala ──
        batal(tab)
        js(tab, """(function(){document.querySelector(
            'input[name="pai-bab"][value="BAB III"]').click();})()""", 1.5)
        d = dom(tab)
        cek('F8a radio kepala pulih + pembuka bersih',
            '"radio":"BAB III"' in d and '"pembuka":null' in d, d)
        n = jumlah_fetch(tab)
        klik_jalan(tab)
        h = hitung_terakhir(tab, n)
        cek('F8b server 3 Token lagi',
            h and h.get('rev') == 3, h)
        batal(tab)

        #  ── F9: nol exception ──
        err = js(tab, "JSON.stringify(window.__err || [])", 0.3)
        cek('F9 nol exception JS', err == '[]', err)

        #  potret buat MATA — tampilan SUB TERPILIH (state 3.1+3.2)
        js(tab, """(function(){document.querySelector(
            'input[name="pai-sub"][value="3.1"]').click();
            document.querySelector(
            'input[name="pai-sub"][value="3.2"]').click();})()""", 1.5)
        potret_tab(tab, '/tmp/fix_3jalur.png')
    finally:
        try:
            import urllib.request
            urllib.request.urlopen(f'{P.CDP}/json/close/{tid}', timeout=5).read()
        except Exception:                                                # noqa: BLE001
            pass
        tab.tutup()

    lulus = sum(1 for _, o, _ in hasil if o)
    gagal = sum(1 for _, o, _ in hasil if not o)
    print(f'\nRINGKASAN: {lulus} LULUS / {gagal} GAGAL')
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
