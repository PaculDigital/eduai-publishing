#!/usr/bin/env bash
# UJI LEWAT DOMAIN (jalur yang user benar-benar pakai) — bukan localhost host.
cd /opt/data/services/eduai-publishing || exit 1

T=$(docker exec eduai-app python3 -c "from app.auth import buat_token; print(buat_token(7))")
C=$(docker exec eduai-app python3 -c "from app.config import SESSION_COOKIE; print(SESSION_COOKIE)")
B="https://eduai.bikinaja.id"
echo "cookie=$C"

echo
echo "=== 1. POST dokumen baru LEWAT DOMAIN ==="
curl -s -o /tmp/db2.json -w 'HTTP %{http_code}\n' --max-time 40 \
  -X POST "$B/api/ai/v1/alur/dokumen-baru" \
  -H 'Content-Type: application/json' -H "Cookie: $C=$T" \
  -d '{"nama_dokumen":"UJI-BAHASA-02Okt26.docx"}'
echo "--- balasan ---"
head -c 400 /tmp/db2.json; echo

FID=$(python3 -c "
import json
try:
    d=json.load(open('/tmp/db2.json'))
    print(d.get('file_id') or d.get('dokumen',{}).get('file_id') or '')
except Exception: print('')")
echo
echo "=== 2. file_id=$FID -> bahasa berkasnya ==="
if [ -n "$FID" ]; then
  docker exec eduai-app python3 -c "
import sqlite3, zipfile, re, collections, os
c = sqlite3.connect('/app/data/eduai.db')
row = c.execute('select nama_simpan, user_id from files where id=?', ($FID,)).fetchone()
print('  DB:', row)
if row:
    p = f'/app/uploads/{row[1]}/{row[0]}'
    print('  berkas:', p, 'ADA' if os.path.exists(p) else 'TIDAK ADA')
    if os.path.exists(p):
        z = zipfile.ZipFile(p)
        d = z.read('word/styles.xml').decode('utf-8','ignore')
        print('  BAHASA:', dict(collections.Counter(re.findall(r'w:lang w:val=\"([^\"]+)\"', d))))
"
else
  echo "  (tidak dapat file_id)"
fi
