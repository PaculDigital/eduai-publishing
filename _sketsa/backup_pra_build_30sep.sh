#!/usr/bin/env bash
# Backup sebelum build image (30Sep26) — titik mundur.
# Pola resmi: image save + tag cadangan + DB checkpoint + kode + cek bisa dipulihkan.
set -uo pipefail
cd /opt/data/services/eduai-publishing

TS=$(date +%Y%m%d-%H%M%S)
D="_arsip/pre-build-centang-$TS"
mkdir -p "$D"

TAG_LIVE=$(docker inspect eduai-app --format '{{.Config.Image}}')
echo "IMAGE LIVE : $TAG_LIVE"

echo "=== A. tag cadangan (pulih instan) ==="
docker tag "$TAG_LIVE" eduai-app:cadangan-pra-build-centang
echo "  → eduai-app:cadangan-pra-build-centang"

echo "=== B. image utuh → tar.gz ==="
docker save "$TAG_LIVE" | gzip -1 > "$D/image-live.tar.gz"
ls -la "$D/image-live.tar.gz" | awk '{print "  size:", $5, "byte"}'

echo "=== C. DB (checkpoint WAL dulu) ==="
docker exec eduai-app python3 -c "
import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
c.commit()
print('  users=', c.execute('SELECT COUNT(*) FROM users').fetchone()[0],
      'files=', c.execute('SELECT COUNT(*) FROM files').fetchone()[0])
c.close()"
docker cp eduai-app:/app/data/eduai.db "$D/eduai.db"

echo "=== D. kode + .env (tanpa cetak isi) ==="
tar czf "$D/kode-app.tar.gz" app/ scripts/ Dockerfile requirements.txt jalankan.sh 2>/dev/null
[ -f .env ] && cp .env "$D/.env" && chmod 600 "$D/.env"

echo "=== E. VERIFIKASI backup bisa dibaca ==="
python3 - "$D/eduai.db" <<'PY'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
print('  integritas:', c.execute('PRAGMA integrity_check').fetchone()[0])
print('  users:', c.execute('SELECT COUNT(*) FROM users').fetchone()[0],
      '| files:', c.execute('SELECT COUNT(*) FROM files').fetchone()[0])
c.close()
PY
tar tzf "$D/kode-app.tar.gz" >/dev/null && echo "  tar kode OK"

echo
echo "BACKUP SELESAI: $D"
ls -la "$D"
