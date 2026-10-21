#!/bin/bash
# Lihat pesan galat lengkap dari tiap provider (kenapa 403/402)
K=$(grep -m1 'api_key: sk-dc0' /opt/data/config.yaml | sed 's/.*api_key: //' | tr -d ' ')
IMG=$(base64 -w0 /tmp/uji_vision.png)

for M in "Xkiro/google/gemini-3.8-flash" "Infron/google/gemini-3.8-flash" "inferhub/glm-4.6v"; do
  echo "────── $M"
  curl -s -m 40 -X POST http://172.17.0.1:20128/v1/chat/completions \
    -H "Content-Type: application/json" -H "Authorization: Bearer $K" \
    -d "{\"model\":\"$M\",\"messages\":[{\"role\":\"user\",\"content\":[{\"type\":\"text\",\"text\":\"warna?\"},{\"type\":\"image_url\",\"image_url\":{\"url\":\"data:image/png;base64,$IMG\"}}]}],\"max_tokens\":30}" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print('   ', str(d.get('error',{}).get('message',''))[:300])"
done
