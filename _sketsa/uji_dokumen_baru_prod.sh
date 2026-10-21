#!/usr/bin/env bash
# UJI NYATA dokumen baru -> bahasa id-ID (path rute BENAR)
cd /opt/data/services/eduai-publishing || exit 1

T=$(docker exec eduai-app python3 -c "from app.auth import buat_token; print(buat_token(7))")
C=$(docker exec eduai-app python3 -c "from app.config import SESSION_COOKIE; print(SESSION_COOKIE)")
echo "cookie=$C token=ada"
echo

echo "=== 1. POST dokumen baru ==="
curl -s -o /tmp/db1.json -w 'HTTP %{http_code}\n' --max-time 30 \
  -X POST "http://127.0.0.1:8100/api/ai/v1/alur/dokumen-baru" \
  -H 'Content-Type: application/json' -H "Cookie: $C=$T" \
  -d '{"nama_dokumen":"UJI-BAHASA-02Okt26.docx"}'
echo "--- balasan ---"
head -c 500 /tmp/db1.json; echo

echo
echo "=== 2. Bahasa berkas hasil (id-ID?) ==="
FID=$(python3 -c "
import json
try:
    d=json.load(open('/tmp/db1.json'))
    print(d.get('file_id') or d.get('dokumen',{}).get('file_id') or '')
except Exception: print('')")
echo "file_id=$FID"

if [ -n "$FID" ]; then
  docker exec eduai-app python3 -c "
import sqlite3, zipfile, re, collections, os, glob
c = sqlite3.connect('/app/data/eduai.db')
row = c.execute('select nama_simpan, user_id from files where id=?', ($FID,)).fetchone()
print('  baris DB:', row)
if row:
    p = f'/app/uploads/{row[1]}/{row[0]}'
    print('  berkas  :', p, '✓ ada' if os.path.exists(p) else '✗ TIDAK ADA')
    if os.path.exists(p):
        z = zipfile.ZipFile(p)
        d = z.read('word/styles.xml').decode('utf-8','ignore')
        hasil = dict(collections.Counter(re.findall(r'w:lang w:val=\"([^\"]+)\"', d)))
        print('  BAHASA  :', hasil)
        print('  zip sehat:', z.testzip() or 'OK')
"
fi
