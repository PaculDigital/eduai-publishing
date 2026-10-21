#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  🚨 WARNING PERMANEN — PERINTAH BOS (16 Sep 2026) 🚨                     ║
# ║                                                                          ║
# ║  "JANGAN PERNAH SEKALI KALI MENCOBA MENAMBAL JIKA ADA ERROR.            ║
# ║   HARUS ANALISA DAN TEMUKAN AKAR MASALAHNYA, DAN KEMBALI KE RUJUKAN     ║
# ║   DOKUMENTASI ATAU MASTER PLAN SEBELUMNYA."                            ║
# ║                                                                          ║
# ║  CARA KERJA WAJIB (jangan dilanggar):                                    ║
# ║   1. REPRODUKSI error dulu — jangan menebak.                             ║
# ║   2. UKUR: pakai alat ukur nyata (pyflakes, grep SELURUH repo, log).     ║
# ║   3. BUKA RUJUKAN: MASTER_PLAN.md / docs / skill ini dulu.              ║
# ║   4. Cari AKAR (kenapa ini bisa terjadi), bukan gejala.                  ║
# ║   5. Perbaiki AKAR-nya + TULIS gerbang/uji supaya tak terulang.          ║
# ║                                                                          ║
# ║  KENAPA: tambalan "benar sekarang" tapi GAGAL di kasus lain.             ║
# ║  BUKTI: 4 tambalan daftar-isi GAGAL → 1 aturan akar awal_isi_naskah().  ║
# ╚══════════════════════════════════════════════════════════════════════════╝
# ═══════════════════════════════════════════════════════════════════════
#  JALANKAN OO — jalankan container OnlyOffice dengan JWT PERMANEN
# ═══════════════════════════════════════════════════════════════════════
#
#  MASALAH YANG DIPECAHKAN
#  ──────────────────────
#  Skrip resmi OnlyOffice (`run-document-server.sh` baris 121) memakai:
#
#      JWT_SECRET=${JWT_SECRET:-$(pwgen -s 32)}
#
#  Artinya kalau env JWT_SECRET KOSONG, secret di-GENERATE ACAK BARU
#  setiap container dinyalakan. Akibatnya:
#
#    - Aplikasi kita (eduai-app) memakai secret LAMA -> editor gagal
#      tanda tangan -> editor MATI DIAM-DIAM setiap restart/rebuild.
#
#  SOLUSI
#  ──────
#  Berikan env JWT_SECRET secara EKSPLISIT saat `docker run`. Secret itu
#  dibaca dari file `.jwt_oo_secret` (permanen, tersimpan di proyek).
#
#  Kalau `.jwt_oo_secret` belum ada, skrip ini:
#    1. Ambil secret dari container yang sedang jalan (kalau ada)
#    2. Atau generate baru
#    3. Simpan ke `.jwt_oo_secret` + siapkan `.env` aplikasi
#
#  CARA PAKAI
#  ──────────
#    bash scripts/jalankan_oo.sh              # buat/nyalakan container
#    bash scripts/jalankan_oo.sh --jwt-baru   # paksa generate JWT baru
#    bash scripts/jalankan_oo.sh --status     # cek saja
# ═══════════════════════════════════════════════════════════════════════
set -uo pipefail

CT=oo-converter
DIR="$(cd "$(dirname "$0")/.." && pwd)"
FILE_JWT="$DIR/.jwt_oo_secret"
FILE_ENV="$DIR/.env"
AKSES="$DIR/_arsip"

HIJAU=$'\033[0;32m'; MERAH=$'\033[0;31m'; KUNING=$'\033[0;33m'
BIRU=$'\033[0;34m'; TEBAL=$'\033[1m'; NORMAL=$'\033[0m'

ok()   { echo "  ${HIJAU}✓${NORMAL} $*"; }
gagal(){ echo "  ${MERAH}✗${NORMAL} $*"; }
info() { echo "  ${BIRU}→${NORMAL} $*"; }
peringatan(){ echo "  ${KUNING}!${NORMAL} $*"; }
judul(){ echo; echo "${TEBAL}${BIRU}═══ $* ═══${NORMAL}"; }

MODE="${1:-jalan}"

# ── Mode: cek status saja ─────────────────────────────────────────────
if [ "$MODE" = "--status" ]; then
    judul "STATUS ONLYOFFICE"
    if ! docker ps --format '{{.Names}}' | grep -qx "$CT"; then
        gagal "Container '$CT' TIDAK JALAN"
        exit 1
    fi
    ok "Container '$CT' jalan"

    S_RT=$(docker exec "$CT" python3 -c "
import json
print(json.load(open('/etc/onlyoffice/documentserver/local.json'))
      ['services']['CoAuthoring']['secret']['browser']['string'])" 2>/dev/null)
    S_FI=$(cat "$FILE_JWT" 2>/dev/null | tr -d '\n')
    S_EN=$(grep -E '^EDUAI_OO_JWT_SECRET=' "$FILE_ENV" 2>/dev/null | cut -d= -f2-)

    info "secret runtime : ${S_RT:0:8}... (${#S_RT} char)"
    info "secret file    : ${S_FI:0:8}... (${#S_FI} char)"
    info "secret .env    : ${S_EN:0:8}... (${#S_EN} char)"

    if [ "$S_RT" = "$S_FI" ] && [ "$S_FI" = "$S_EN" ]; then
        ok "${TEBAL}SEMUA COCOK — JWT PERMANEN ✓${NORMAL}"
    else
        gagal "${TEBAL}ADA YANG TIDAK COCOK${NORMAL}"
        echo "     Jalankan: bash scripts/jalankan_oo.sh"
    fi
    exit 0
fi

# ── 1. Tentukan secret permanen ───────────────────────────────────────
judul "1. Tentukan JWT secret PERMANEN"

if [ "$MODE" = "--jwt-baru" ]; then
    info "mode --jwt-baru: generate secret baru"
    SECRET=$(head -c 24 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c 32)
    echo "$SECRET" > "$FILE_JWT"; chmod 600 "$FILE_JWT"
    ok "secret baru dibuat"
elif [ -s "$FILE_JWT" ]; then
    SECRET=$(cat "$FILE_JWT" | tr -d '\n')
    ok "memakai secret permanen dari .jwt_oo_secret (${#SECRET} char)"
elif docker ps --format '{{.Names}}' | grep -qx "$CT"; then
    # Ambil dari container yang sedang jalan — JANGAN buang secret lama!
    SECRET=$(docker exec "$CT" python3 -c "
import json
print(json.load(open('/etc/onlyoffice/documentserver/local.json'))
      ['services']['CoAuthoring']['secret']['browser']['string'])" 2>/dev/null)
    if [ -n "$SECRET" ]; then
        echo "$SECRET" > "$FILE_JWT"; chmod 600 "$FILE_JWT"
        ok "secret diadopsi dari container yang jalan (${#SECRET} char)"
    else
        gagal "tidak bisa baca secret dari container"
        exit 1
    fi
else
    info "belum ada secret — generate baru"
    SECRET=$(head -c 24 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c 32)
    echo "$SECRET" > "$FILE_JWT"; chmod 600 "$FILE_JWT"
    ok "secret baru dibuat (${#SECRET} char)"
fi

# ── 2. Samakan dengan .env aplikasi ──────────────────────────────────
judul "2. Samakan secret dengan .env aplikasi"

if [ ! -f "$FILE_ENV" ]; then
    gagal ".env tidak ditemukan: $FILE_ENV"
    exit 1
fi

S_EN=$(grep -E '^EDUAI_OO_JWT_SECRET=' "$FILE_ENV" 2>/dev/null | cut -d= -f2- || echo "")
if [ "$S_EN" = "$SECRET" ]; then
    ok ".env sudah cocok"
else
    /opt/data/.venv/bin/python3 - "$SECRET" "$FILE_ENV" <<'PYEOF'
import re, sys
sec, fn = sys.argv[1], sys.argv[2]
s = open(fn).read()
if re.search(r'^EDUAI_OO_JWT_SECRET=', s, re.M):
    s = re.sub(r'^EDUAI_OO_JWT_SECRET=.*$', f'EDUAI_OO_JWT_SECRET={sec}', s, flags=re.M)
else:
    s += f'\nEDUAI_OO_JWT_SECRET={sec}\n'
open(fn, 'w').write(s)
print('  .env diperbarui')
PYEOF
    chmod 600 "$FILE_ENV"
    ok ".env disamakan"
fi

# ── 3. (Re)buat container dengan env JWT ─────────────────────────────
if [ "$MODE" = "--jwt-baru" ] || ! docker ps -a --format '{{.Names}}' | grep -qx "$CT"; then
    judul "3. Buat container '$CT' dengan JWT permanen"

    if docker ps -a --format '{{.Names}}' | grep -qx "$CT"; then
        info "container lama dihapus (volume dipertahankan)"
        docker stop "$CT" >/dev/null 2>&1
        docker rm "$CT" >/dev/null 2>&1
    fi

    docker run -d --name "$CT" --network eduai-net --network-alias oo-converter \
        --restart unless-stopped \
        -p 127.0.0.1:18081:80 \
        -e JWT_ENABLED=true \
        -e JWT_SECRET="$SECRET" \
        -e JWT_HEADER=Authorization \
        -e ALLOW_PRIVATE_IP_ADDRESS=true \
        -e ALLOW_META_IP_ADDRESS=true \
        -e USE_UNAUTHORIZED_STORAGE=false \
        -v onlyoffice_data:/var/www/onlyoffice/Data \
        -v onlyoffice_fonts:/usr/share/fonts/truetype/custom \
        -v onlyoffice_lib:/var/lib/onlyoffice \
        -v onlyoffice_logs:/var/log/onlyoffice \
        onlyoffice/documentserver:latest >/dev/null

    ok "container dibuat (restart=unless-stopped, JWT dari env)"
    info "menunggu siap..."
    for i in $(seq 1 45); do
        sleep 3
        if docker exec "$CT" sh -c "curl -s -o /dev/null \
            http://127.0.0.1/web-apps/apps/api/documents/api.js" 2>/dev/null; then
            break
        fi
    done
    sleep 4
    ok "container siap"
else
    judul "3. Container sudah jalan"
    ok "container '$CT' aktif"
fi

# ── 4. Verifikasi secret benar-benar terpakai ────────────────────────
judul "4. Verifikasi JWT permanen"

S_RT=$(docker exec "$CT" python3 -c "
import json
print(json.load(open('/etc/onlyoffice/documentserver/local.json'))
      ['services']['CoAuthoring']['secret']['browser']['string'])" 2>/dev/null)

echo "  runtime : ${S_RT:0:8}... (${#S_RT} char)"
echo "  file    : ${SECRET:0:8}... (${#SECRET} char)"

if [ "$S_RT" = "$SECRET" ]; then
    ok "${TEBAL}JWT PERMANEN AKTIF — tidak akan berubah lagi ✓${NORMAL}"
else
    gagal "${TEBAL}JWT TIDAK COCOK${NORMAL}"
    echo "  Kemungkinan: env JWT_SECRET tidak terbaca oleh container."
    echo "  Periksa: docker inspect $CT --format '{{json .Config.Env}}'"
    exit 1
fi

# ── 5. Pastikan setelan nginx juga terpasang ─────────────────────────
judul "5. Setelan nginx (CORS, tutup, WebSocket)"

PERLU=0
docker exec "$CT" test -f /etc/nginx/includes/eduai-cors.conf 2>/dev/null || PERLU=1
docker exec "$CT" test -f /etc/nginx/includes/eduai-tutup.conf 2>/dev/null || PERLU=1
docker exec "$CT" grep -q 'eduai-cors' /etc/nginx/conf.d/ds.conf 2>/dev/null || PERLU=1
docker exec "$CT" grep -q 'proxy_set_header Upgrade' \
    /etc/nginx/includes/ds-docservice.conf 2>/dev/null || PERLU=1

# ── 5a. WAJIB: KUNCI secure_link HARUS SAMA ──────────────────────────
#  TERBUKTI 16Sep26: kunci BEDA -> nginx SELALU menolak Editor.bin (403)
#  -> editor "tidak bisa dimuat" -> DOKUMEN TIDAK PERNAH TERMUAT.
#  Gejala di layar TIDAK menyebut 403, jadi diperiksa DI SINI secara
#  eksplisit (dulu hanya ikut lewat perbaiki_oo.sh kalau ada yang lain
#  hilang -> bisa TERLEWAT).
SEC_NGINX=$(docker exec "$CT" sh -c \
    "grep -oP 'secure_link_secret \\K[A-Za-z0-9]+' /etc/nginx/conf.d/ds.conf 2>/dev/null" 2>/dev/null)
SEC_LOCAL=$(docker exec "$CT" sh -c \
    "grep -oP 'secretString\"\\s*:\\s*\"\\K[^\"]+' /etc/onlyoffice/documentserver/local.json 2>/dev/null" 2>/dev/null)

if [ -z "$SEC_NGINX" ] || [ -z "$SEC_LOCAL" ]; then
    peringatan "kunci secure_link tidak terbaca — memeriksa OO"
    PERLU=1
elif [ "$SEC_NGINX" != "$SEC_LOCAL" ]; then
    gagal "KUNCI secure_link BEDA — Editor.bin akan SELALU 403 (editor mati)!"
    PERLU=1
else
    ok "kunci secure_link COCOK"
fi

if [ "$PERLU" -eq 1 ]; then
    peringatan "ada setelan nginx yang hilang — memperbaiki otomatis"
    bash "$DIR/scripts/perbaiki_oo.sh" 2>&1 | grep -E '✓|✗|→' | head -20
else
    ok "semua setelan nginx terpasang"
fi

# ── 5b. Pastikan WARNA TAB (Kolaborasi + AI) terpasang ───────────────
#  PENTING: dicek TERPISAH dari nginx. Sebelumnya perbaiki_oo.sh hanya
#  dipanggil kalau ada setelan nginx yang hilang — sehingga container
#  yang nginx-nya lengkap akan MELEWATKAN pemasangan CSS tab.
judul "5b. Warna tab Kolaborasi + AI (permanen)"

DS_TAB=/var/www/onlyoffice/documentserver/web-apps/apps
N_TAB=$(docker exec "$CT" sh -c "grep -l 'EDUAI-TAB-COLLAB' $DS_TAB/*/main/resources/css/app.css 2>/dev/null | wc -l" || echo 0)
N_AI=$(docker exec "$CT" sh -c "grep -l 'EDUAI-TAB-COLLAB-AI' $DS_TAB/*/main/resources/css/app.css 2>/dev/null | wc -l" || echo 0)

if [ "${N_TAB:-0}" -ge 5 ] && [ "${N_AI:-0}" -ge 5 ]; then
    ok "CSS tab terpasang (Kolaborasi $N_TAB/5, AI $N_AI/5)"
else
    peringatan "CSS tab belum lengkap (Kolaborasi ${N_TAB:-0}/5, AI ${N_AI:-0}/5) — memasang"
    bash "$DIR/scripts/perbaiki_oo.sh" 2>&1 | grep -E '✓|✗|→' | head -20
fi

# ── 6. Pastikan BRANDING EduAi terpasang ─────────────────────────────
judul "6. Branding EduAi (logo + About)"

DS=/var/www/onlyoffice/documentserver/web-apps/apps
BRAND_PERLU=0
SZ=$(docker exec "$CT" sh -c "stat -c %s $DS/common/main/resources/img/header/dark-logo_s.svg 2>/dev/null" || echo 0)
[ "${SZ:-0}" -gt 20000 ] 2>/dev/null || BRAND_PERLU=1
docker exec "$CT" grep -q 'EduAi INOVASI' "$DS/common/main/lib/view/About.js" 2>/dev/null || BRAND_PERLU=1
N=$(docker exec "$CT" sh -c "grep -l 'EDUAI-ABOUT-FIX' $DS/*/main/resources/css/app.css 2>/dev/null | wc -l")
[ "${N:-0}" -ge 5 ] || BRAND_PERLU=1

if [ "$BRAND_PERLU" -eq 1 ]; then
    peringatan "branding hilang/belum lengkap — memasang otomatis"
    bash "$DIR/scripts/pasang_branding_oo.sh" 2>&1 | grep -E '✓|✗|→' | head -15
else
    ok "branding EduAi terpasang (logo header + About)"
fi

judul "SELESAI"
echo "  OnlyOffice siap. Editor: https://eduai.bikinaja.id"
echo
echo "  Cek kapan saja:  bash scripts/jalankan_oo.sh --status"
echo "  Perbaiki OO   :  bash scripts/perbaiki_oo.sh"
echo "  Pasang branding: bash scripts/pasang_branding_oo.sh"
echo
