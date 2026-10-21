#!/bin/bash
# Tes 9router: apakah model vision sudah pulih?
K=$(grep -m1 'api_key: sk-dc0' /opt/data/config.yaml | sed 's/.*api_key: //' | tr -d ' ')
for i in 1 2 3; do
  code=$(curl -s -m 25 -o /tmp/v.json -w "%{http_code}" \
    -X POST http://172.17.0.1:20128/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $K" \
    -d '{"model":"ag/gemini-3.8-flash-high","messages":[{"role":"user","content":"ok"}],"max_tokens":5}')
  echo "  coba $i: HTTP $code $(head -c 140 /tmp/v.json)"
  if [ "$code" = "200" ]; then break; fi
  sleep 5
done
