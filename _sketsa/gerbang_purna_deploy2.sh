#!/usr/bin/env bash
#  Salin gerbang ke container PASCA-DEPLOY lalu jalankan (07 Okt 2026)
#  CATATAN: file _gerbang_*.py TIDAK ikut image (memang alat uji).
cd /opt/data/services/eduai-publishing || exit 1
for g in _gerbang_skema_jev.py _gerbang_halaman_mutu.py _gerbang_jev_mata.py _gerbang_jev_optimasi.py _gerbang_sot.py; do
  docker cp "$g" eduai-app:/app/ >/dev/null 2>&1 || echo "  (gagal salin $g)"
done
echo "gerbang disalin"
for g in _gerbang_skema_jev.py _gerbang_halaman_mutu.py _gerbang_jev_mata.py _gerbang_jev_optimasi.py _gerbang_sot.py; do
  docker exec -w /app eduai-app timeout 500 python3 -u "$g" >"/tmp/pd2_$g.txt" 2>&1
  kode=$?
  printf '%-28s EXIT=%s  %s\n' "$g" "$kode" "$(grep -E 'HASIL|TOTAL' "/tmp/pd2_$g.txt" | tail -1)"
done
