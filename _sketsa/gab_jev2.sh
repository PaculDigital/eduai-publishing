#!/usr/bin/env bash
#  Salin + jalankan gerbang Jev yang tersisa (07 Okt 2026)
cd /opt/data/services/eduai-publishing || exit 1
docker cp _gerbang_jev_mata.py eduai-app:/app/ || exit 1
docker cp _gerbang_jev_optimasi.py eduai-app:/app/ || exit 1
echo "cp OK"
for g in _gerbang_jev_mata.py _gerbang_jev_optimasi.py; do
  docker exec -w /app eduai-app timeout 500 python3 -u "$g" >"/tmp/o_$g.txt" 2>&1
  kode=$?
  echo "$g EXIT=$kode -> $(grep TOTAL "/tmp/o_$g.txt" | tail -1)"
done
