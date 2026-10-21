#!/usr/bin/env bash
# Cari penyebab HTTP 403 pada POST /alur/dokumen-baru
cd /opt/data/services/eduai-publishing || exit 1
T=$(docker exec eduai-app python3 -c "from app.auth import buat_token; print(buat_token(7))")
C=$(docker exec eduai-app python3 -c "from app.config import SESSION_COOKIE; print(SESSION_COOKIE)")
echo "cookie=$C"

echo
echo "=== A. POST langsung ke CONTAINER (localhost:8100) ==="
curl -s -o /tmp/r1.txt -w 'HTTP %{http_code}\n' --max-time 20 \
  -X POST http://127.0.0.1:8100/alur/dokumen-baru \
  -H 'Content-Type: application/json' -H "Cookie: $C=$T" \
  -d '{"nama_dokumen":"UJI-A.docx"}'
head -c 300 /tmp/r1.txt; echo

echo
echo "=== B. GET /api/... untuk cek login tembus? ==="
curl -s -o /tmp/r2.txt -w 'HTTP %{http_code}\n' --max-time 15 \
  -H "Cookie: $C=$T" http://127.0.0.1:8100/api/profil 2>/dev/null
head -c 200 /tmp/r2.txt; echo

echo
echo "=== C. Lewat domain ==="
curl -s -o /tmp/r3.txt -w 'HTTP %{http_code}\n' --max-time 25 \
  -X POST https://eduai.bikinaja.id/alur/dokumen-baru \
  -H 'Content-Type: application/json' -H "Cookie: $C=$T" \
  -d '{"nama_dokumen":"UJI-B.docx"}'
head -c 300 /tmp/r3.txt; echo

echo
echo "=== D. Middleware / pagar yang bisa 403 ==="
grep -rn '403' app/main.py | head -10
