#!/bin/bash
# Render bukti dua gerbang: jalan di container (ambil data), render di host.
cd /opt/data/services/eduai-publishing || exit 1
mkdir -p /tmp/gg
docker exec eduai-app mkdir -p /tmp/gg
echo "=== TAHAP 1 (container): siapkan data + HTML ==="
docker cp _render_gerbang.py eduai-app:/tmp/render_gerbang.py
docker exec eduai-app python3 /tmp/render_gerbang.py
echo
echo "=== salin ke host ==="
docker exec eduai-app sh -c "cat /tmp/gg/jatah_penuh.html" > /tmp/gg/jatah_penuh.html
echo "  jatah_penuh.html $(stat -c%s /tmp/gg/jatah_penuh.html) byte"
echo
echo "=== TAHAP 2 (host): render PNG ==="
timeout 150 /opt/data/chrome/chrome --headless=new --no-sandbox --disable-gpu \
  --hide-scrollbars --window-size=900,1300 --screenshot=/tmp/gg/jatah_penuh.png \
  --virtual-time-budget=12000 --run-all-compositor-stages-before-draw \
  "file:///tmp/gg/jatah_penuh.html" 2>/dev/null
echo "  jatah_penuh.png -> $(stat -c%s /tmp/gg/jatah_penuh.png 2>/dev/null || echo GAGAL) byte"
