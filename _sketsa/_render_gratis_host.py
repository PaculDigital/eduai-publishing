"""Render halaman GRATIS (panel ajak upgrade) — dijalankan di HOST."""
import subprocess
from pathlib import Path

SD = Path('/tmp/sd')
CHROME = '/opt/data/chrome/chrome'

SKRIP = """
<script>
(function () {
  var DATA = __DATA__;
  var _f = window.fetch;
  window.fetch = function (url) {
    var s = String(url);
    if (s.indexOf('/api/paket') === 0)
      return Promise.resolve({ok:true, json:function(){return Promise.resolve(DATA.paket);}});
    if (s.indexOf('/api/addon') === 0)
      return Promise.resolve({ok:true, json:function(){return Promise.resolve(DATA.addon);}});
    return _f.apply(this, arguments);
  };
  window.addEventListener('load', function () {
    setTimeout(function () {
      // Pemicu seperti gerbang asli: panggil tawarkanAddon(sebab).
      // Untuk gratis → panel "ajak upgrade" yang muncul, BUKAN popup.
      if (window.tawarkanAddon) window.tawarkanAddon('Folder Anda sudah penuh.');
      else alert('tawarkanAddon TIDAK ADA');
    }, 500);
  });
})();
</script>
"""

VARIAN = (('gratis_folder', 900, 1250), ('gratis_hp', 420, 1400))

for nama, w, h in VARIAN:
    base = SD / 'gratis_folder.html'
    data = SD / 'data_gratis.json'
    if not base.exists() or not data.exists():
        print('  XX %s tidak lengkap' % nama)
        continue
    html = base.read_text(encoding='utf-8')
    skrip = SKRIP.replace('__DATA__', data.read_text(encoding='utf-8'))
    html = html.replace('</body>', skrip + '</body>', 1)
    p = SD / ('siap_%s.html' % nama)
    p.write_text(html, encoding='utf-8')

    # Cek JS benar-benar memanggil panel, bukan popup
    png = SD / ('gratis_%s.png' % nama.replace('gratis_', ''))
    subprocess.run([CHROME, '--headless=new', '--no-sandbox', '--disable-gpu',
                    '--hide-scrollbars', '--window-size=%d,%d' % (w, h),
                    '--screenshot=' + str(png),
                    '--virtual-time-budget=10000',
                    '--run-all-compositor-stages-before-draw',
                    'file://' + str(p)], capture_output=True, timeout=150)
    print('  %-14s -> %s byte'
          % (png.name, png.stat().st_size if png.exists() else 'GAGAL'))

# cek fungsi tawarkanAddon ada di HTML
h = (SD / 'gratis_folder.html').read_text(encoding='utf-8')
print('  tawarkanAddon ada=%d | tampilAjakUpgrade ada=%d | ajak-tombol ada=%d'
      % (h.count('function tawarkanAddon'), h.count('function tampilAjakUpgrade'),
         h.count('ajak-tombol')))
