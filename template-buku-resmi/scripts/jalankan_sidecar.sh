#!/bin/bash
# Buat/jalankan ulang container sidecar buku (Opsi B2) — OPERATOR, SEKALI.
# JALANKAN DARI TERMINAL HOST (tempat perintah `docker exec hermes` biasa
# dijalankan), BUKAN dari dalam hermes. Path /root/.hermes/... adalah path
# HOST yang dilihat docker daemon — jangan diganti ke /opt/data/services/...
# (itu pohon data app di host, bukan checkout; hermes melihat checkout
# sebagai /opt/data/services/... HANYA karena /root/.hermes di-mount ke
# /opt/data di dalam hermes).
# Skrip ini butuh berkas cabang ini (checkout pasca-merge, atau checkout
# cabang untuk uji pra-merge).
# TIDAK menyentuh jalankan.sh / app / image app: sidecar hidup sendiri di
# jaringan eduai-net, seperti oo-converter. Bila container ini dihapus,
# buat ulang dengan perintah ini (buku web gagal jelas, bukan diam-diam).
#
# Pakai: bash jalankan_sidecar.sh KUNCI_SIDECAR
#   KUNCI_SIDECAR = nilai yang SAMA dengan EDUAI_SIDECAR_KUNCI di .env app.
#   Kunci TIDAK pernah ditulis ke berkas — hanya diteruskan ke container.
set -e
KUNCI="${1:-}"
if [ -z "$KUNCI" ]; then
    echo "Pakai: bash jalankan_sidecar.sh KUNCI_SIDECAR" >&2
    exit 2
fi
cd "$(dirname "$0")"
docker build -f Dockerfile.sidecar -t wordcraft-sidecar:1 . >/dev/null
docker rm -f wordcraft-sidecar >/dev/null 2>&1 || true
docker run -d --name wordcraft-sidecar --network eduai-net \
    --restart unless-stopped \
    -v /root/.hermes/services/eduai-publishing/template-buku-resmi:/mesin:ro \
    -v /root/.hermes/services/wordcraft-uji:/wordcraft:ro \
    -v /root/.hermes/services/pdftotext-arah:/pdftotext:ro \  # pdftotext-arah: direktori yang benar lewat bind mount (pdftotext asli rusak lewat mount)
    -e WORDCRAFT_CLI=/wordcraft/bin/wordcraft-cli \
    -e PATH=/pdftotext/bin:/usr/local/bin:/usr/bin:/bin \
    -e EDUAI_SIDECAR_KUNCI="$KUNCI" \
    wordcraft-sidecar:1
sleep 2
docker exec wordcraft-sidecar python3 -c \
    "import urllib.request,json;print(json.loads(urllib.request.urlopen('http://127.0.0.1:8131/sehat',timeout=10).read()))"
echo "Sidecar jalan. App wajib punya EDUAI_SIDECAR_URL=http://wordcraft-sidecar:8131 + kunci yang sama."
