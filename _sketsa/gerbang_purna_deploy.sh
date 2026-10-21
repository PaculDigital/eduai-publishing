#!/usr/bin/env bash
#  Gerbang purna-deploy UI pesan mutu (07 Okt 2026)
cd /opt/data/services/eduai-publishing || exit 1
for g in _gerbang_skema_jev.py _gerbang_halaman_mutu.py _gerbang_jev_mata.py _gerbang_jev_optimasi.py _gerbang_sot.py; do
  docker exec -w /app eduai-app timeout 500 python3 -u "$g" >"/tmp/pd_$g.txt" 2>&1
  kode=$?
  printf '%-28s EXIT=%s  %s\n' "$g" "$kode" "$(grep -E 'HASIL|TOTAL' "/tmp/pd_$g.txt" | tail -1)"
done
echo ""
echo "=== SOT ==="
python3 sot.py --periksa >/tmp/pd_sot.txt 2>&1
echo "sot.py --periksa EXIT=$?"
tail -3 /tmp/pd_sot.txt
