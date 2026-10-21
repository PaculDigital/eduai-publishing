#!/bin/bash
# Cari model VISION 9router yang masih hidup (bisa lihat gambar).
K=$(grep -m1 'api_key: sk-dc0' /opt/data/config.yaml | sed 's/.*api_key: //' | tr -d ' ')
IMG=$(base64 -w0 /tmp/sd/gratis_folder.png 2>/dev/null | head -c 200000)

for M in "ag/gemini-3.8-flash-high" "cb/gemini-2.5-flash" "cb/gemini-3.0-flash" \
         "cb/gemini-2.5-pro" "cb/gpt-5.6-luna" "cb/deepseek-v4-flash" "cb/glm-4.6"; do
  code=$(curl -s -m 40 -o /tmp/vv.json -w "%{http_code}" \
    -X POST http://172.17.0.1:20128/v1/chat/completions \
    -H "Content-Type: application/json" -H "Authorization: Bearer $K" \
    -d "{\"model\":\"$M\",\"messages\":[{\"role\":\"user\",\"content\":\"Balas satu kata: HALO\"}],\"max_tokens\":10}")
  pesan=$(head -c 110 /tmp/vv.json | tr -d '\n')
  echo "  $M -> HTTP $code | $pesan"
done
