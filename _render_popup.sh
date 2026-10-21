#!/bin/bash
# Perbaiki typo JS + render popup (Chrome di host)
cd /tmp/pp || exit 1

for n in penulis gratis; do
  python3 - "$n" <<'PYEOF'
import sys
n = sys.argv[1]
p = '/tmp/pp/auto_%s.html' % n
t = open(p, encoding='utf-8').read()
t = t.replace('window.fetunction(u,o)', 'window.fetch = function(u,o)')
open(p, 'w', encoding='utf-8').write(t)
print('  %s diperbaiki: %s' % (n, 'window.fetch = function' in t))
PYEOF
done

echo
echo "=== RENDER (Chrome host) ==="
for n in penulis gratis; do
  timeout 115 /opt/data/chrome/chrome --headless=new --no-sandbox --disable-gpu \
    --hide-scrollbars --window-size=900,1150 --screenshot=/tmp/pp/pp_$n.png \
    --virtual-time-budget=5000 "file:///tmp/pp/auto_$n.html" 2>/dev/null
  echo "  pp_$n.png -> $(stat -c%s /tmp/pp/pp_$n.png 2>/dev/null || echo GAGAL)"
done

echo
echo "=== versi HP 420px ==="
timeout 115 /opt/data/chrome/chrome --headless=new --no-sandbox --disable-gpu \
  --hide-scrollbars --window-size=420,1250 --screenshot=/tmp/pp/pp_hp.png \
  --virtual-time-budget=5000 "file:///tmp/pp/auto_penulis.html" 2>/dev/null
echo "  pp_hp.png -> $(stat -c%s /tmp/pp/pp_hp.png 2>/dev/null || echo GAGAL)"
