#!/bin/bash
# Tes model dengan prefix yang BENAR (CB/, Xkiro/, Infron/, Byn/)
K=$(grep -m1 'api_key: sk-dc0' /opt/data/config.yaml | sed 's/.*api_key: //' | tr -d ' ')
IMG=$(base64 -w0 /tmp/uji_vision.png)

for M in "CB/gemini-3.8-flash-high" "CB/gpt-5.6-luna" "Byn/gemini-3.8-flash-high" \
         "Xkiro1/google/gemini-3.8-flash" "Infron/google/gemini-3.8-flash" \
         "inferhub/ag/gemini-3.8-flash-high"; do
  code=$(curl -s -m 45 -o /tmp/vx.json -w "%{http_code}" \
    -X POST http://172.17.0.1:20128/v1/chat/completions \
    -H "Content-Type: application/json" -H "Authorization: Bearer $K" \
    -d "{\"model\":\"$M\",\"messages\":[{\"role\":\"user\",\"content\":[{\"type\":\"text\",\"text\":\"Gambar: dominan warna apa? 2 kata.\"},{\"type\":\"image_url\",\"image_url\":{\"url\":\"data:image/png;base64,$IMG\"}}]}],\"max_tokens\":40}")
  hasil=$(python3 -c "
import json
try:
    d=json.load(open('/tmp/vx.json'))
    if 'choices' in d: print('OK  '+d['choices'][0]['message']['content'][:70].replace(chr(10),' '))
    else: print('ERR '+str(d.get('error',{}).get('message',''))[:100])
except Exception as e: print('??',str(e)[:60])
")
  echo "  $M -> $code | $hasil"
done
