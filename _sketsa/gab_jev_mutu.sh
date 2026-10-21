#!/usr/bin/env bash
#  Jalankan gerbang yang relevan sesi Jev + Mutu (07 Okt 2026)
cd /opt/data/services/eduai-publishing || exit 1
python3 - <<'PYEOF'
import pathlib
p = pathlib.Path('sot.py'); s = p.read_text()
s = s.replace("ALAT: jalankan 17 gerbang dari dalam container",
              "ALAT: jalankan 18 gerbang dari dalam container")
p.write_text(s)
print("sot.py: 17->18 gerbang")
PYEOF
echo "=== GERBANG JEV + MUTU ==="
for g in _gerbang_skema_jev.py _gerbang_halaman_mutu.py _gerbang_jev_mata.py _gerbang_jev_optimasi.py; do
  docker exec -w /app eduai-app timeout 500 python3 -u "$g" >"/tmp/o_$g.txt" 2>&1
  kode=$?
  echo "$g EXIT=$kode -> $(grep TOTAL "/tmp/o_$g.txt" | tail -1)"
done
