#!/usr/bin/env bash
# Uji BERGIGI gerbang editor: rusak kunci sengaja -> HARUS GAGAL -> pulihkan.
# WAJIB: pulihkan di try/finally supaya produksi tidak ditinggal rusak.
set -uo pipefail
cd /opt/data/services/eduai-publishing

echo "=== 1. Simpan kunci ASLI (tanpa cetak isi) ==="
ASLI=$(docker exec oo-converter sh -c \
  "grep -oP 'secure_link_secret \K[A-Za-z0-9]+' /etc/nginx/conf.d/ds.conf | head -1")
echo "  panjang kunci asli: ${#ASLI}"

echo "=== 2. RUSAK sengaja (ganti kunci nginx dengan nilai palsu) ==="
docker exec oo-converter sh -c \
  "sed -i 's|set \$secure_link_secret .*|set \$secure_link_secret PALSU123PALSU1234;|' /etc/nginx/conf.d/ds.conf"
docker exec oo-converter sh -c "nginx -s reload"
sleep 2

echo "=== 3. Gerbang HARUS GAGAL (kunci beda) ==="
out=$(bash scripts/periksa_editor.sh 2>&1); kode=$?
echo "$out" | grep -E '✗|⛔|✓ kunci'
echo "  EXIT=$kode  (harap 1)"

echo
echo "=== 4. PULIHKAN kunci asli + reload ==="
docker exec oo-converter sh -c \
  "sed -i 's|set \$secure_link_secret .*|set \$secure_link_secret ${ASLI};|' /etc/nginx/conf.d/ds.conf"
docker exec oo-converter sh -c "nginx -s reload"
sleep 2

echo "=== 5. Verifikasi PULIH (sidik jari sama lagi) ==="
docker exec oo-converter sh -c '
S1=$(grep -oP "secure_link_secret \K[A-Za-z0-9]+" /etc/nginx/conf.d/ds.conf | head -1)
S2=$(grep -oP "secretString\"\s*:\s*\"\K[^\"]+" /etc/onlyoffice/documentserver/local.json | head -1)
echo "  nginx sha8=$(printf %s "$S1" | sha256sum | cut -c1-8)"
echo "  local sha8=$(printf %s "$S2" | sha256sum | cut -c1-8)"
[ "$S1" = "$S2" ] && echo "  STATUS: PULIH ✅" || echo "  STATUS: MASIH BEDA ❌"
'
echo "=== 6. Gerbang lagi (harap LULUS) ==="
bash scripts/periksa_editor.sh >/dev/null 2>&1; echo "  EXIT=$?"
