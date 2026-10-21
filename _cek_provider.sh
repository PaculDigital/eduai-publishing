#!/bin/bash
# Lihat daftar provider 9router + statusnya
K=$(grep -m1 'api_key: sk-dc0' /opt/data/config.yaml | sed 's/.*api_key: //' | tr -d ' ')
echo "=== /v1/models (semua model tersedia) ==="
curl -s -m 20 -H "Authorization: Bearer $K" http://172.17.0.1:20128/v1/models -o /tmp/mm.json -w "HTTP %{http_code}\n"
python3 - <<'PYEOF'
import json
try:
    d = json.load(open('/tmp/mm.json'))
    ids = [m['id'] for m in d.get('data', [])]
    print('  total model: %d' % len(ids))
    prov = {}
    for i in ids:
        p = i.split('/')[0]
        prov.setdefault(p, []).append(i)
    for p, v in sorted(prov.items()):
        print('  %-14s %d model (contoh: %s)' % (p, len(v), v[0]))
except Exception as e:
    print('  err:', e)
    print(open('/tmp/mm.json').read()[:300])
PYEOF
echo
echo "=== container 9router ==="
docker ps --format '{{.Names}}\t{{.Status}}' 2>/dev/null | grep -i "9router\|router" || echo "(tidak ada container 9router)"
