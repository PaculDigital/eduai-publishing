#!/bin/bash
# Bersihkan tab CDP yang menumpuk (aturan: TAB YATIM bikin gerbang gantung).
# JANGAN pkill chrome — cukup tutup tab-nya.
for id in $(curl -s -m 5 http://127.0.0.1:9333/json/list \
            | grep -o '"id": "[^"]*"' | cut -d'"' -f4); do
  curl -s -m 4 "http://127.0.0.1:9333/json/close/$id" >/dev/null 2>&1
done
sleep 2
sisa=$(curl -s -m 5 http://127.0.0.1:9333/json/list | grep -c '"type": "page"')
echo "sisa tab page: $sisa"
