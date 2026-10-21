#!/usr/bin/env python3
"""Render popup — versi terakhir yang ANDAL.

Pelajaran dari percobaan sebelumnya:
  1. Popup harus dibuka lewat tombol aslinya (`onclick="bukaTopup()"`).
  2. Data harus disuntikkan SEBELUM popup dibuka (kalau tidak → error).
  3. `--virtual-time-budget` kecil bikin Chrome "selesai" sebelum fetch
     data selesai → popup kosong. Pakai waktu lebih besar + tunggu gambar.
"""
import json
import subprocess
from pathlib import Path

PP = Path('/tmp/pp')
CHROME = '/opt/data/chrome/chrome'

SKRIP = """
<script>
(function () {
  /* Data SUNGGUHAN dari server (lihat _popup_1_ambil.sh) */
  var DATA = __DATA__;
  var _fetchAsli = window.fetch;
  window.fetch = function (url) {
    var s = String(url);
    if (s.indexOf('/api/paket') === 0) {
      return Promise.resolve({ ok: true, json: function () {
        return Promise.resolve(DATA.paket); } });
    }
    if (s.indexOf('/api/addon') === 0) {
      return Promise.resolve({ ok: true, json: function () {
        return Promise.resolve(DATA.addon); } });
    }
    return _fetchAsli.apply(this, arguments);
  };

  /* Buka popup lewat tombol aslinya, lalu TUNGGU sampai kartu terbentuk. */
  function cobaBuka(sisa) {
    var tb = document.querySelector('button[onclick*="bukaTopup"]');
    if (tb) { tb.click(); }
    else if (typeof window.bukaTopup === 'function') { window.bukaTopup(); }
    else if (sisa > 0) { return setTimeout(function(){ cobaBuka(sisa-1); }, 150); }

    /* Tandai kalau kartu AddOn benar-benar sudah tergambar. */
    var n = 0;
    var tik = setInterval(function () {
      n++;
      var kartu = document.querySelectorAll('.kartu-addon');
      window.__SIAP = (kartu.length > 0) ? 'ya:' + kartu.length : 'tunggu';
      if (kartu.length > 0 || n > 40) {
        clearInterval(tik);
        /* Kunci hasil akhir untuk dibaca setelah render */
        document.title = 'SIAP ' + window.__SIAP;
      }
    }, 100);
  }
  window.addEventListener('load', function () { cobaBuka(5); });
})();
</script>
"""


def render(nama):
    base = PP / ('base_%s.html' % nama)
    data = PP / ('data_%s.json' % nama)
    html = base.read_text(encoding='utf-8')
    skrip = SKRIP.replace('__DATA__', data.read_text(encoding='utf-8'))
    html = html.replace('</body>', skrip + '</body>', 1)
    out = PP / ('siap_%s.html' % nama)
    out.write_text(html, encoding='utf-8')

    assert 'DATA.paket' in html, 'data tidak tersuntik'
    assert 'fetunction' not in html, 'ada typo'

    for tag, w, h in (('', 900, 1250), ('_hp', 420, 1400)):
        png = PP / ('final_%s%s.png' % (nama, tag))
        subprocess.run(
            [CHROME, '--headless=new', '--no-sandbox', '--disable-gpu',
             '--hide-scrollbars', '--window-size=%d,%d' % (w, h),
             '--screenshot=' + str(png),
             '--virtual-time-budget=15000',       # beri waktu fetch selesai
             '--run-all-compositor-stages-before-draw',
             'file://' + str(out)], capture_output=True, timeout=150)
        print('  %s -> %s byte'
              % (png.name, png.stat().st_size if png.exists() else 'GAGAL'))


for nama in ('penulis', 'gratis'):
    render(nama)
