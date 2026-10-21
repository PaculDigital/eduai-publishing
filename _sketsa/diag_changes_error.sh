#!/usr/bin/env bash
# Diagnosa "changesError: Failed to fetch" dari OO — cari callback yang gagal.
set -uo pipefail
cd /opt/data/services/eduai-publishing

echo "════ 1. Alamat callback yang dikirim ke OO ════"
docker exec eduai-app python3 -c "
import sys; sys.path.insert(0,'/app')
from app.config import *
from app.onlyoffice import url_browser, url_internal
import inspect
print('  url_browser   :', url_browser())
try: print('  url_internal  :', url_internal())
except Exception as e: print('  url_internal  : (tak ada)', e)
" 2>&1 | head -10

echo
echo "════ 2. Dari DALAM oo-converter: bisakah menjangkau app? ════"
for U in "http://172.20.0.2:8000/health" "http://eduai-app:8000/health" "http://localhost:8000/health"; do
  printf '  %-40s -> ' "$U"
  docker exec oo-converter sh -c "curl -s -o /dev/null -w '%{http_code}' -m 8 '$U'" 2>/dev/null || echo "GAGAL"
  echo
done

echo
echo "════ 3. IP app sekarang ════"
docker inspect eduai-app --format '  {{range $k,$v := .NetworkSettings.Networks}}{{$k}}={{.IPAddress}} {{end}}'

echo
echo "════ 4. Alamat simpan/unduh yang BENAR-BENAR dipanggil OO (log app) ════"
docker logs --since 15m eduai-app 2>&1 | grep -oE 'POST /oo/simpan/[a-f0-9]+|GET /oo/unduh/[a-f0-9]+' | sort | uniq -c | tail -10

echo
echo "════ 5. Jejak dari sisi oo-converter (alamat yang ia hubungi) ════"
docker logs --since 15m oo-converter 2>&1 | grep -viE '^tail:' | grep -oE 'http://[0-9a-zA-Z._-]+:[0-9]+' | sort | uniq -c | tail -10
