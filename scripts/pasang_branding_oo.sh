#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
#  PASANG BRANDING OO — pasang ulang branding EduAi ke container OO
# ═══════════════════════════════════════════════════════════════════════
#
#  KENAPA SKRIP INI ADA
#  ─────────────────────
#  Branding EduAi (logo header + About) hidup sebagai FILE DI DALAM
#  container `oo-converter`. Karena image OnlyOffice tidak bisa kita
#  ubah (image resmi), file itu HILANG setiap container dibuat ulang.
#
#  Skrip ini memasang kembali dari sumber PERMANEN di repo:
#     oo-branding/header/  -> SVG logo header (bar biru)
#     oo-branding/about/   -> About.js + logo PNG dialog About
#     oo-branding/css/     -> suntikan CSS (matikan :before OnlyOffice)
#
#  Aman dijalankan berkali-kali (idempoten).
#
#  CARA PAKAI
#  ──────────
#    bash scripts/pasang_branding_oo.sh          # pasang + verifikasi
#    bash scripts/pasang_branding_oo.sh --cek    # periksa saja
#
#  CATATAN
#  ───────
#  Setelah pasang, WAJIB purge cache Cloudflare kalau lewat domain:
#    python3 scripts/purge_cf_aset.py
# ═══════════════════════════════════════════════════════════════════════
set -uo pipefail

CT="${OO_CONTAINER:-oo-converter}"
DIR="$(cd "$(dirname "$0")/.." && pwd)"
BRAND="$DIR/oo-branding"

HIJAU=$'\033[0;32m'; MERAH=$'\033[0;31m'; KUNING=$'\033[0;33m'
BIRU=$'\033[0;34m'; TEBAL=$'\033[1m'; NORMAL=$'\033[0m'
ok()   { echo "  ${HIJAU}✓${NORMAL} $*"; }
gagal(){ echo "  ${MERAH}✗${NORMAL} $*"; }
info() { echo "  ${BIRU}→${NORMAL} $*"; }
judul(){ echo; echo "${TEBAL}${BIRU}═══ $* ═══${NORMAL}"; }

MODE="${1:-pasang}"
DS=/var/www/onlyoffice/documentserver/web-apps/apps
MASALAH=0

judul "0. Cek container"
if ! docker ps --format '{{.Names}}' | grep -qx "$CT"; then
    gagal "container '$CT' TIDAK JALAN"
    echo
    echo "  Jalankan dulu:  bash scripts/jalankan_oo.sh"
    exit 1
fi
ok "container '$CT' jalan"

judul "1. Cek sumber permanen"
for F in "$BRAND/header/dark-logo_s.svg" \
         "$BRAND/header/header-logo_s.svg" \
         "$BRAND/about/About.js" \
         "$BRAND/about/logo-eduai-about.png"; do
    if [ -s "$F" ]; then
        printf "  %-46s${HIJAU}✓ %s B${NORMAL}\n" "$(basename "$F")" "$(stat -c %s "$F")"
    else
        printf "  %-46s${MERAH}✗ TIDAK ADA${NORMAL}\n" "$(basename "$F")"
        MASALAH=1
    fi
done
[ "$MASALAH" -eq 1 ] && { echo; echo "  Sumber tidak lengkap — STOP."; exit 1; }

# ── Mode cek ─────────────────────────────────────────────────────────
if [ "$MODE" = "--cek" ]; then
    judul "2. Status di container"
    SZ=$(docker exec "$CT" sh -c "stat -c %s $DS/common/main/resources/img/header/dark-logo_s.svg 2>/dev/null" || echo 0)
    [ "${SZ:-0}" -gt 20000 ] 2>/dev/null \
        && ok "logo header biru terpasang (${SZ} B)" \
        || { gagal "logo header biru masih bawaan (${SZ:-0} B)"; MASALAH=1; }

    docker exec "$CT" grep -q 'EduAi INOVASI' "$DS/common/main/lib/view/About.js" 2>/dev/null \
        && ok "data About.js ada" \
        || { gagal "data About.js TIDAK ada"; MASALAH=1; }

    N=$(docker exec "$CT" sh -c "grep -l 'EDUAI-ABOUT-FIX' $DS/*/main/resources/css/app.css 2>/dev/null | wc -l")
    [ "${N:-0}" -ge 5 ] && ok "CSS fix $N/5 editor" \
                        || { gagal "CSS fix hanya ${N:-0}/5"; MASALAH=1; }

    docker exec "$CT" test -s "$DS/common/main/resources/img/about/logo-eduai-about.png" 2>/dev/null \
        && ok "file logo About ada" \
        || { gagal "file logo About TIDAK ada"; MASALAH=1; }

    echo
    [ "$MASALAH" -eq 0 ] && echo "  ${HIJAU}${TEBAL}BRANDING OK ✓${NORMAL}" \
                         || echo "  ${MERAH}${TEBAL}BRANDING BELUM LENGKAP ✗${NORMAL}"
    exit "$MASALAH"
fi

# ── Mode pasang ──────────────────────────────────────────────────────
judul "2. Salin logo header (SVG, + .gz)"
docker exec "$CT" mkdir -p "$DS/common/main/resources/img/header" 2>/dev/null
docker cp "$BRAND/header/dark-logo_s.svg"   "$CT:$DS/common/main/resources/img/header/dark-logo_s.svg"   >/dev/null
docker cp "$BRAND/header/header-logo_s.svg" "$CT:$DS/common/main/resources/img/header/header-logo_s.svg" >/dev/null
# .gz WAJIB sebanding — nginx OO pakai `gzip_static on`, kalau .gz lama
# tetap ada maka yang diserve versi LAMA.
for N in dark-logo_s header-logo_s; do
    docker exec "$CT" sh -c "gzip -9 -c $DS/common/main/resources/img/header/$N.svg \
        > $DS/common/main/resources/img/header/$N.svg.gz"
done
ok "dark-logo_s.svg + header-logo_s.svg (+ .gz)"

judul "3. Salin About.js (+ .gz)"
docker cp "$BRAND/about/About.js" "$CT:$DS/common/main/lib/view/About.js" >/dev/null
docker exec "$CT" sh -c "gzip -9 -c $DS/common/main/lib/view/About.js \
    > $DS/common/main/lib/view/About.js.gz"
ok "About.js (+ .gz)"

judul "4. Salin logo About (PNG)"
docker exec "$CT" mkdir -p "$DS/common/main/resources/img/about" 2>/dev/null
docker cp "$BRAND/about/logo-eduai-about.png" \
    "$CT:$DS/common/main/resources/img/about/logo-eduai-about.png" >/dev/null
ok "logo-eduai-about.png"

judul "5. Suntik CSS (matikan :before OnlyOffice + logo besar)"
# CSS ditulis lewat python DI DALAM container (argumen panjang tidak aman).
python3 "$DIR/scripts/perbaiki_logo_about.py" >/dev/null 2>&1 \
    && ok "CSS fix 5/5 editor" \
    || { gagal "gagal suntik CSS"; MASALAH=1; }

judul "6. Verifikasi"
SZ=$(docker exec "$CT" sh -c "stat -c %s $DS/common/main/resources/img/header/dark-logo_s.svg" 2>/dev/null || echo 0)
[ "${SZ:-0}" -gt 20000 ] 2>/dev/null && ok "logo header (${SZ} B)" \
                                     || { gagal "logo header masih bawaan"; MASALAH=1; }
N=$(docker exec "$CT" sh -c "grep -l 'EDUAI-ABOUT-FIX' $DS/*/main/resources/css/app.css 2>/dev/null | wc -l")
[ "${N:-0}" -ge 5 ] && ok "CSS fix $N/5 editor" \
                    || { gagal "CSS fix hanya ${N:-0}/5"; MASALAH=1; }
docker exec "$CT" grep -q 'EduAi INOVASI' "$DS/common/main/lib/view/About.js" \
    && ok "data About.js" || { gagal "data About.js hilang"; MASALAH=1; }

echo
if [ "$MASALAH" -eq 0 ]; then
    echo "  ${HIJAU}${TEBAL}BRANDING TERPASANG ✓${NORMAL}"
    echo
    echo "  ${KUNING}PENTING:${NORMAL} kalau user akses lewat domain, purge cache CF:"
    echo "    python3 scripts/purge_cf_aset.py"
else
    echo "  ${MERAH}${TEBAL}ADA YANG BELUM BERES ✗${NORMAL}"
    exit 1
fi
