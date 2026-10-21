#!/bin/bash
# inferhub/ag/gemini-3.8-flash-high HTTP 200 → lihat isi lengkap balasan
K=$(grep -m1 'api_key: sk-dc0' /opt/data/config.yaml | sed 's/.*api_key: //' | tr -d ' ')
IMG=$(base64 -w0 /tmp/uji_vision.png)
curl -s -m 60 -X POST http://172.17.0.1:20128/v1/chat/completions \
  -H "Content-Type: application/json" -H "Authorization: Bearer $K" \
  -d "{\"model\":\"inferhub/ag/gemini-3.8-flash-high\",\"messages\":[{\"role\":\"user\",\"content\":[{\"type\":\"text\",\"text\":\"Gambar ini dominan warna apa? Jawab 3 kata.\"},{\"type\":\"image_url\",\"image_url\":{\"url\":\"data:image/png;base64,$IMG\"}}]}],\"max_tokens\":60}" \
  -o /tmp/ag.json -D /tmp/ag.head
echo "=== HEADER ==="; head -4 /tmp/ag.head
echo "=== BODY (mentah, 700 char) ==="
head -c 700 /tmp/ag.json
echo
echo "=== struktur ==="
python3 -c "
import json,re
t=open('/tmp/ag.json',encoding='utf-8',errors='replace').read()
# mungkin SSE: ambil potongan data
if t.startswith('data:') or 'data: ' in t[:200]:
    print('  bentuk: SSE stream')
    for ln in t.splitlines()[:12]:
        if ln.startswith('data: '): print('   ', ln[:160])
else:
    d=json.loads(t)
    print('  keys:', list(d.keys()))
    if 'choices' in d: print('  ISI:', repr(d['choices'][0]['message']['content'])[:200])
"