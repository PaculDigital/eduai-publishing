"""Suntik data ke HTML + buka popup + render (dijalankan di HOST).

Merender 4 varian:
  folder        → kartu saran + lipatan TERTUTUP
  folder_buka   → kartu saran + lipatan TERBUKA (bukti panel oranye nyatu)
  storage       → saran storage
  manual        → tanpa saran, katalog terbuka
"""
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
      __BUKA__
      var tb = document.querySelector('button[onclick*="bukaTopup"]');
      if (tb) tb.click();
    }, 450);
  });
})();
</script>
"""

# nama → (sumber data, buka lipatan?)
VARIAN = (
    ('folder', 'folder', False),
    ('folder_buka', 'folder', True),
    ('storage', 'storage', False),
    ('manual', 'manual', False),
)

for nama, sumber, buka in VARIAN:
    base = SD / ('%s.html' % sumber)
    data = SD / ('data_%s.json' % sumber)
    if not base.exists() or not data.exists():
        print('  XX %s tidak lengkap' % nama)
        continue
    html = base.read_text(encoding='utf-8')
    # Buka lipatan SEBELUM klik tombol — supaya <details> sudah terbuka saat foto
    isi_buka = ("document.getElementById('lipat-lain').open = true;"
                if buka else '')
    skrip = (SKRIP.replace('__DATA__', data.read_text(encoding='utf-8'))
                  .replace('__BUKA__', isi_buka))
    html = html.replace('</body>', skrip + '</body>', 1)
    p = SD / ('siap_%s.html' % nama)
    p.write_text(html, encoding='utf-8')
    print('  %-12s siap=%.1fKB | kata "Lihat pilihan lain"=%d'
          % (nama, len(html) / 1024, html.count('Lihat pilihan lain')))

    for tag, w, h in (('', 900, 1250), ('_hp', 420, 1400)):
        png = SD / ('sadar_%s%s.png' % (nama, tag))
        subprocess.run([CHROME, '--headless=new', '--no-sandbox', '--disable-gpu',
                        '--hide-scrollbars', '--window-size=%d,%d' % (w, h),
                        '--screenshot=' + str(png),
                        '--virtual-time-budget=12000',
                        '--run-all-compositor-stages-before-draw',
                        'file://' + str(p)], capture_output=True, timeout=150)
        print('     %s -> %s byte'
              % (png.name, png.stat().st_size if png.exists() else 'GAGAL'))
