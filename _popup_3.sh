#!/bin/bash
# Salin data JSON dari container ke host, lalu render.
cd /opt/data/services/eduai-publishing || exit 1
for n in penulis gratis; do
  docker exec eduai-app sh -c "cat /tmp/pp/data_$n.json" > /tmp/pp/data_$n.json
  echo "  data_$n.json -> $(stat -c%s /tmp/pp/data_$n.json) byte"
done
echo
python3 _popup_2_render.py
