#!/bin/bash
# 1. Cek SALDO InferHub
# 2. Lihat provider/kredensial yang terdaftar di 9router
echo "=== 1. SALDO InferHub (management API) ==="
K=$(grep -oP 'sk-[A-Za-z0-9_\-]{20,}' /opt/data/services/inferhub/NOTES.md | head -1)
curl -s -m 25 -H "Authorization: Bearer $K" https://inferhub.dev/api/me -o /tmp/me.json -w "HTTP %{http_code}\n"
head -c 500 /tmp/me.json
echo
echo
echo "=== 2. KONTAINER 9router — cari konfigurasi provider ==="
docker inspect 9router --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}' 2>/dev/null
echo
docker exec 9router sh -c 'ls -la /app 2>/dev/null | head -20' 2>/dev/null
