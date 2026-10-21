#!/bin/bash
D=/opt/data/services/eduai-publishing
Z=/tmp/loa2_x/tridarma-loa

echo "== 1. pakai versi ISI-ISI (15 token) =="
cp $Z/agent/template-loa-jemt-agent.html $D/app/templates/loa/loa-jemt.html
echo "   ok"

echo "== 2. pastikan nomor baru =="
sed -i 's/0857-2050-5555/0851-7813-8514/g' $D/app/templates/loa/loa-jemt.html
grep -c "0851-7813-8514" $D/app/templates/loa/loa-jemt.html

echo "== 3. cek token & ttd =="
/opt/data/.venv/bin/python3 - <<'PY'
import re, pathlib
p = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/loa-jemt.html')
s = p.read_text(encoding='utf-8')
tok = sorted(set(re.findall(r'\{\{\s*([a-zA-Z_]+)\s*\}\}', s)))
print('   token:', len(tok), '->', ', '.join(tok))
print('   ada img ttd?', 'tanda-tangan.png' in s)
print('   ada bintang?', 'ttd-bintang' in s, '(harus False)')
print('   nomor WA lama?', '0857-2050-5555' in s, '(harus False)')
PY

echo "== 4. PNG ttd masih ada? =="
ls -la $D/app/templates/loa/ | grep -E "png|jpg"
