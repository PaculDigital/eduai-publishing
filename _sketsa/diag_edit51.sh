#!/bin/bash
# Diagnosa lanjutan: apakah docservice MEMANGGIL /oo/unduh, atau pakai cache lama?
# Tangkap log saat buka /edit/51, dengan timestamp presisi.
set -u
cd /opt/data/services/eduai-publishing

TOKEN=$(docker exec eduai-app python3 -c "from app.auth import buat_token; print(buat_token(3))")
CK=$(docker exec eduai-app python3 -c "from app.config import SESSION_COOKIE; print(SESSION_COOKIE)")

echo "=== T0: $(date -u +%H:%M:%S) ==="
MARK=$(date -u +%H:%M:%S)

# jalankan pembuka editor di latar, 60 dtk saja
(EDUAI_SESSION=$TOKEN EDUAI_COOKIE_NAME=$CK EDUAI_FID=51 timeout 75 python3 _sketsa/tunggu_editor_render.py > /tmp/tunggu51.log 2>&1) &

# sambil itu pantau log app tiap 5 dtk
for i in $(seq 1 14); do
  sleep 5
  echo "--- t+$((i*5))s"
  docker logs --since 8s eduai-app 2>&1 | grep -E "unduh|Editor.bin|simpan|cache/files" | tail -4
done
wait
echo
echo "=== RINGKASAN SELURUH JEJAK (sejak awal) ==="
docker logs --since 2m eduai-app 2>&1 | grep -E "unduh|Editor.bin|simpan|cache/files" | tail -25
echo
echo "=== LOG OO (error/docservice) ==="
docker logs --since 2m oo-converter 2>&1 | grep -viE '^tail:' | tail -25
