#!/bin/bash
# Cari model VISION yang hidup dari provider yang MASIH ADA.
K=$(grep -m1 'api_key: sk-dc0' /opt/data/config.yaml | sed 's/.*api_key: //' | tr -d ' ')
echo "=== kandidat model vision (dari /v1/models) ==="
python3 - <<'PYEOF'
import json
d = json.load(open('/tmp/mm.json'))
ids = [m['id'] for m in d.get('data', [])]
pat = ('gemini', 'gpt-5', 'gpt-4', 'claude', 'qwen-vl', 'vl', 'vision', 'glm-4')
for i in sorted(ids):
    if any(p in i.lower() for p in pat):
        print('  ', i)
PYEOF
