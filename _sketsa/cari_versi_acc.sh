#!/bin/bash
D=/opt/data/services/eduai-publishing
echo "== versi LoA yang tersimpan (yang Bos ACC tadi) =="
ls -la $D/app/templates/loa/ 2>/dev/null
echo
echo "== apakah ada salinan lama di image/arsip? =="
ls -la /tmp/uji_loa18/ 2>/dev/null | head -5
echo
echo "== cari template loa lain di proyek =="
find /opt/data/services/eduai-publishing -name "*loa*" -name "*.html" 2>/dev/null | head -10
