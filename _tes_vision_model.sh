#!/bin/bash
# Tes model vision: kirim gambar KECIL + tanya isinya.
K=$(grep -m1 'api_key: sk-dc0' /opt/data/config.yaml | sed 's/.*api_key: //' | tr -d ' ')
# gambar uji: buat PNG kecil berisi teks "WULAN" via ImageMagick/fallback
python3 - <<'PYEOF'
import base64, struct, zlib
# PNG 120x40 putih dengan blok hitam (bukan teks — cukup untuk cek "bisa lihat")
W,H=120,40
raw=b''
for y in range(H):
    row=b'\x00'
    for x in range(W):
        if 20<x<100 and 10<y<30: row+=b'\x00\x00\x00'
        else: row+=b'\xff\xff\xff'
    raw+=row
def ch(t,d):
    c=t+d; return struct.pack('>I',len(d))+c+struct.pack('>I',zlib.crc32(c))
png=b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',W,H,8,2,0,0,0))+ch(b'IDAT',zlib.compress(raw))+ch(b'IEND',b'')
open('/tmp/uji_vision.png','wb').write(png)
print('  gambar uji dibuat:', len(png), 'byte')
PYEOF
IMG=$(base64 -w0 /tmp/uji_vision.png)
for M in "Xkiro/google/gemini-3.8-flash" "Infron/google/gemini-3.8-flash" \
         "inferhub/gemini-3.8-flash" "inferhub/glm-4.6v" "Xkiro/z-ai/glm-4.6v" \
         "Infron/qwen/qwen3-vl-plus" "inferhub/lifelike-vision"; do
  code=$(curl -s -m 45 -o /tmp/vr.json -w "%{http_code}" \
    -X POST http://172.17.0.1:20128/v1/chat/completions \
    -H "Content-Type: application/json" -H "Authorization: Bearer $K" \
    -d "{\"model\":\"$M\",\"messages\":[{\"role\":\"user\",\"content\":[{\"type\":\"text\",\"text\":\"Gambar ini dominan warna apa? Jawab 2 kata saja.\"},{\"type\":\"image_url\",\"image_url\":{\"url\":\"data:image/png;base64,$IMG\"}}]}],\"max_tokens\":40}")
  isi=$(python3 -c "
import json,sys
try:
    d=json.load(open('/tmp/vr.json'))
    if 'choices' in d: print('OK:', d['choices'][0]['message']['content'][:70].replace(chr(10),' '))
    else: print('ERR:', str(d)[:90])
except Exception as e: print('PARSE-ERR', str(e)[:60])
")
  echo "  $M -> HTTP $code | $isi"
done
