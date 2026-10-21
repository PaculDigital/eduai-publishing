#!/usr/bin/env bash
# Cek: server vitiasi :8001 memuat KODE MANA + apakah suntikan rusak ada.
echo "=== 1. suntikan 'if False + pagar' ada di salinan? (host) ==="
grep -c 'PAGAR OPSI A' /tmp/uji_root/app/ai.py || echo 0
grep -c 'if False and hasil is None' /tmp/uji_root/app/ai.py || echo 0
grep -c 'if hasil is None and pipa_jalan' /tmp/uji_root/app/ai.py || echo 0

echo "=== 2. KODE MANA yang diproses :8001 benar-benar import? ==="
cat > /tmp/uji_root/probe.py <<'PYEOF'
import sys
from pathlib import Path
sys.path.insert(0, '/tmp/uji_root')
import app.ai as ai
src = Path(ai.__file__).read_text()
print("modul   :", ai.__file__)
print("ada sunTikk 'if False':", "if False and hasil is None" in src)
print("ada pagar Opsi A     :", "PAGAR OPSI A" in src)
print("sys.path[0:3]        :", sys.path[:3])
PYEOF
docker exec -e PYTHONPATH=/tmp/uji_root eduai-app python /tmp/uji_root/probe.py 2>&1

echo "=== 3. error di server.log :8001 ==="
grep -iE 'error|traceback|module' /tmp/uji_root/server.log | head -10 || echo BERSIH

echo "=== 4. nodev :8001 — path module lewat env server ==="
tr '\0' '\n' < /proc/1240/environ | grep -E 'PYTHONPATH|EDUAI_' || echo 'TIDAK ADA PYTHONPATH/EDUAI di proses'