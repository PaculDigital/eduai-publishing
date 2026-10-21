#!/usr/bin/env bash
# Uji PASCA-BUILD (30Sep26): 3 fix centang masuk image + editor hidup + data utuh.
set -uo pipefail
cd /opt/data/services/eduai-publishing

echo "════ 1. IMAGE & CONTAINER ════"
docker ps --filter name=eduai-app --format '  container: {{.Names}} | {{.Status}}'
docker inspect eduai-app --format '  image    : {{.Config.Image}}'
docker inspect eduai-app --format '  jaringan : {{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'

echo
echo "════ 2. FIX 3 CENTANG ADA DI DALAM CONTAINER? ════"
N_CT=$(docker exec eduai-app grep -c 'bersihSeleksi\|lepasKartu' /app/app/templates/editor.html)
N_HOST=$(grep -c 'bersihSeleksi\|lepasKartu' app/templates/editor.html)
M_CT=$(docker exec eduai-app md5sum /app/app/templates/editor.html | awk '{print $1}')
M_HOST=$(md5sum app/templates/editor.html | awk '{print $1}')
echo "  penanda container=$N_CT host=$N_HOST"
echo "  md5 container=$M_CT"
echo "  md5 host     =$M_HOST"
[ "$M_CT" = "$M_HOST" ] && echo "  ✅ md5 COCOK — fix dari IMAGE (bukan docker cp)" || echo "  ❌ md5 BEDA"

echo
echo "════ 3. INTEGRITAS KODE DI IMAGE (bukan cuma container) ════"
IMG=$(docker inspect eduai-app --format '{{.Config.Image}}')
docker run --rm --entrypoint sh "$IMG" -c \
  'echo "  penanda di IMAGE: $(grep -c "bersihSeleksi\|lepasKartu" /app/app/templates/editor.html)"; echo "  md5 di IMAGE    : $(md5sum /app/app/templates/editor.html | cut -d" " -f1)"'

echo
echo "════ 4. DATA UTUH (DB) ════"
docker exec eduai-app python3 -c "
import sqlite3
c=sqlite3.connect('/app/data/eduai.db')
print('  users=', c.execute('SELECT COUNT(*) FROM users').fetchone()[0],
      'files=', c.execute('SELECT COUNT(*) FROM files').fetchone()[0],
      'proses_ai=', c.execute('SELECT COUNT(*) FROM proses_ai').fetchone()[0])
c.close()"

echo
echo "════ 5. KESEHATAN PUBLIK ════"
printf '  /health   : '; curl -s --max-time 15 https://eduai.bikinaja.id/health; echo
printf '  api.js    : '; curl -s -o /dev/null -w '%{http_code}\n' --max-time 15 https://eduai.bikinaja.id/oo/aset/web-apps/apps/api/documents/api.js

echo
echo "════ 6. GERBANG EDITOR (secure_link) ════"
bash scripts/periksa_editor.sh 2>&1 | grep -E '✓|✗|!|LULUS|GAGAL'
