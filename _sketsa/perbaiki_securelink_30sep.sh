#!/bin/bash
# Perbaiki AKAR secure_link beda di oo-converter (403 Editor.bin -> editor -4)
# Backup dulu, lalu jalankan perbaiki_oo.sh, lalu buktikan kunci COCOK.
set -u
cd /opt/data/services/eduai-publishing

D="_arsip/pre-oo-securelink-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$D"
docker cp oo-converter:/etc/nginx/conf.d/ds.conf "$D/ds.conf"
docker cp oo-converter:/etc/onlyoffice/documentserver/local.json "$D/local.json"
echo "BACKUP: $D"
ls -la "$D"

echo "=== SEBELUM: sidik jari kunci (isi TIDAK dicetak) ==="
docker exec oo-converter sh -c '
S1=$(grep -oP "secure_link_secret \K[A-Za-z0-9]+" /etc/nginx/conf.d/ds.conf 2>/dev/null | head -1)
S2=$(grep -oP "secretString\"\s*:\s*\"\K[^\"]+" /etc/onlyoffice/documentserver/local.json 2>/dev/null | head -1)
echo "ds.conf   len=${#S1} sha8=$(printf %s "$S1" | sha256sum | cut -c1-8)"
echo "local.json len=${#S2} sha8=$(printf %s "$S2" | sha256sum | cut -c1-8)"
[ "$S1" = "$S2" ] && echo "STATUS: SAMA" || echo "STATUS: BEDA"
'

echo
echo "=== JALANKAN perbaiki_oo.sh ==="
bash scripts/perbaiki_oo.sh 2>&1 | tail -60

echo
echo "=== SESUDAH: sidik jari kunci ==="
docker exec oo-converter sh -c '
S1=$(grep -oP "secure_link_secret \K[A-Za-z0-9]+" /etc/nginx/conf.d/ds.conf 2>/dev/null | head -1)
S2=$(grep -oP "secretString\"\s*:\s*\"\K[^\"]+" /etc/onlyoffice/documentserver/local.json 2>/dev/null | head -1)
echo "ds.conf   len=${#S1} sha8=$(printf %s "$S1" | sha256sum | cut -c1-8)"
echo "local.json len=${#S2} sha8=$(printf %s "$S2" | sha256sum | cut -c1-8)"
[ "$S1" = "$S2" ] && echo "STATUS: SAMA  <-- HARAP" || echo "STATUS: BEDA  <-- MASIH RUSAK"
'
