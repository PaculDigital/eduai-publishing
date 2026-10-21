#!/bin/bash
# Render popup dengan cara ANDAL: klik tombol "+ Tambah Kuota" via JS
# (bukan memanggil window.bukaTopup yang bisa belum terdefinisi).
cd /tmp/pp || exit 1

for n in penulis gratis; do
  python3 - "$n" <<'PYEOF'
import sys
n = sys.argv[1]
p = '/tmp/pp/auto_%s.html' % n
t = open(p, encoding='utf-8').read()

# Buang suntikan lama (yang gagal), pasang yang baru.
import re
t = re.sub(r'<script>\s*\n\(function\(\)\{\s*\n var _f=window\.fetch.*?</script>',
           '', t, flags=re.S)

baru = """
<script>
(function () {
  function buka() {
    // Cari tombol asli di halaman (teks "+ Tambah Kuota") lalu klik.
    var btns = document.querySelectorAll('button, a');
    for (var i = 0; i < btns.length; i++) {
      var tx = (btns[i].textContent || '').toLowerCase();
      if (tx.indexOf('tambah kuota') >= 0) {
        btns[i].click();
        window.__DIBUKA = 'klik-tombol';
        return true;
      }
    }
    // Cadangan: panggil fungsinya kalau ada.
    if (typeof window.bukaTopup === 'function') {
      window.bukaTopup();
      window.__DIBUKA = 'fungsi';
      return true;
    }
    window.__DIBUKA = 'GAGAL';
    return false;
  }
  window.addEventListener('load', function () {
    setTimeout(buka, 400);
    setTimeout(buka, 1200);   // percobaan kedua kalau yang pertama terlalu awal
  });
})();
</script>
"""
t = t.replace('</body>', baru + '</body>', 1)
open(p, 'w', encoding='utf-8').write(t)
print('  %s: ok' % n)
PYEOF
done

echo
echo "=== RENDER ==="
for n in penulis gratis; do
  timeout 115 /opt/data/chrome/chrome --headless=new --no-sandbox --disable-gpu \
    --hide-scrollbars --window-size=900,1200 --screenshot=/tmp/pp/pp2_$n.png \
    --virtual-time-budget=7000 "file:///tmp/pp/auto_$n.html" 2>/dev/null
  echo "  pp2_$n.png -> $(stat -c%s /tmp/pp/pp2_$n.png 2>/dev/null || echo GAGAL)"
done
