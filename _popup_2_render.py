#!/usr/bin/env python3
"""Tahap 2: gabung DATA + skrip auto-buka jadi satu halaman, lalu render.

Dipakai bersama _popup_1_ambil.sh (yang mengisi base_*.html + data_*.json).
"""
import json
import subprocess
from pathlib import Path

PP = Path('/tmp/pp')
CHROME = '/opt/data/chrome/chrome'

SKRIP = """
<script>
/* ═══ RENDER UJI POPUP ═══════════════════════════════════════════════════
   Kenapa begini: kalau halaman dibuka dari file://, fetch('/api/paket')
   GAGAL → popup cuma menampilkan "Tidak bisa memuat daftar paket".
   Jadi data SUNGGUHAN dari server (diambil di tahap 1) disuntikkan di sini.
   Tampilan yang digambar JS = sama dengan yang dilihat user di produksi. */
(function () {
  var _fetchAsli = window.fetch;
  var DATA = __DATA__;
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

  function buka() {
    var btns = document.querySelectorAll('button, a');
    for (var i = 0; i < btns.length; i++) {
      var tx = (btns[i].textContent || '').toLowerCase();
      if (tx.indexOf('tambah kuota') >= 0) { btns[i].click(); return true; }
    }
    return false;
  }
  window.addEventListener('load', function () {
    setTimeout(buka, 350);
    setTimeout(buka, 1500);   // cadangan kalau yang pertama terlalu awal
  });
})();
</script>
"""

for nama in ('penulis', 'gratis'):
    base = PP / ('base_%s.html' % nama)
    data = PP / ('data_%s.json' % nama)
    if not base.exists() or not data.exists():
        print('  ✗ %s tidak lengkap — dilewati' % nama)
        continue
    html = base.read_text(encoding='utf-8')
    skrip = SKRIP.replace('__DATA__', data.read_text(encoding='utf-8'))
    # HANYA satu suntikan, tepat sebelum </body>
    html = html.replace('</body>', skrip + '</body>', 1)
    out = PP / ('siap_%s.html' % nama)
    out.write_text(html, encoding='utf-8')
    # verifikasi: data ADA dan tidak ada typo
    ok_data = 'DATA.paket' in html and '"paket"' in html
    ok_typo = 'fetunction' not in html
    print('  %-8s siap=%.1fKB | data=%s | bebas typo=%s'
          % (nama, len(html) / 1024, ok_data, ok_typo))
    assert ok_data and ok_typo, 'suntikan %s tidak sah' % nama

    for tag, w, h in (('', 900, 1200), ('_hp', 420, 1300)):
        png = PP / ('popup_%s%s.png' % (nama, tag))
        subprocess.run(
            [CHROME, '--headless=new', '--no-sandbox', '--disable-gpu',
             '--hide-scrollbars', '--window-size=%d,%d' % (w, h),
             '--screenshot=' + str(png), '--virtual-time-budget=7000',
             'file://' + str(out)], capture_output=True, timeout=115)
        print('     %s -> %s byte'
              % (png.name, png.stat().st_size if png.exists() else 'GAGAL'))
