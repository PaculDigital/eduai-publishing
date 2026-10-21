#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  🚨 WARNING PERMANEN — PERINTAH BOS (16 Sep 2026) 🚨                     ║
# ║  "JANGAN PERNAH SEKALI KALI MENCOBA MENAMBAL JIKA ADA ERROR. HARUS       ║
# ║   ANALISA DAN TEMUKAN AKAR MASALAHNYA, DAN KEMBALI KE RUJUKAN            ║
# ║   DOKUMENTASI ATAU MASTER PLAN SEBELUMNYA."                             ║
# ║  CARA: (1) REPRODUKSI (2) UKUR pakai alat nyata (3) BUKA RUJUKAN         ║
# ║  MASTER_PLAN/dokumen dulu (4) cari AKAR bukan gejala (5) perbaiki AKAR   ║
# ║  + pasang gerbang/uji agar tak terulang.                                ║
# ║  KENAPA: tambalan benar sekarang tapi GAGAL di kasus lain.              ║
# ╚══════════════════════════════════════════════════════════════════════════╝
# ═══════════════════════════════════════════════════════════════════════
#  CEK CEPAT EDUAI — diagnosa 5 titik rawan dalam satu perintah
# ═══════════════════════════════════════════════════════════════════════
#  Pakai saat: editor kosong / "no logic document" / 403 / 404 / 502
#
#    bash scripts/cek_cepat.sh
# ═══════════════════════════════════════════════════════════════════════
set -uo pipefail

CT=oo-converter
APP=eduai-app
AKTIF=/etc/nginx/conf.d/ds.conf
LOCAL=/etc/onlyoffice/documentserver/local.json

HIJAU=$'\033[0;32m'; MERAH=$'\033[0;31m'; KUNING=$'\033[0;33m'
BIRU=$'\033[0;34m'; TEBAL=$'\033[1m'; NORMAL=$'\033[0m'

ok()   { echo "  ${HIJAU}✓${NORMAL} $*"; }
gagal(){ echo "  ${MERAH}✗${NORMAL} $*"; }
info() { echo "  ${BIRU}→${NORMAL} $*"; }
judul(){ echo; echo "${TEBAL}${BIRU}═══ $* ═══${NORMAL}"; }

echo "${TEBAL}CEK CEPAT EDUAI${NORMAL} — $(date '+%d %b %Y %H:%M')"

# ── 1. Container hidup? ───────────────────────────────────────────────
judul "1. Container"
for c in "$APP" "$CT"; do
    if docker ps --format '{{.Names}}' | grep -qx "$c"; then
        UPTIME=$(docker ps --filter "name=$c" --format '{{.Status}}')
        ok "$c — $UPTIME"
    else
        gagal "$c TIDAK JALAN"
    fi
done

# ── 2. Secret secure_link sama? (penyebab 403 /cache/files) ───────────
judul "2. Secure link (penyebab Editor.bin 403)"
SEC_NGINX=$(docker exec "$CT" sh -c \
    "grep -oP 'secure_link_secret \\K[A-Za-z0-9]+' $AKTIF 2>/dev/null" 2>/dev/null)
SEC_LOCAL=$(docker exec "$CT" sh -c \
    "grep -oP 'secretString\"\\s*:\\s*\"\\K[^\"]+' $LOCAL 2>/dev/null" 2>/dev/null)
info "nginx ds.conf : ${SEC_NGINX:0:6}... (${#SEC_NGINX} char)"
info "local.json    : ${SEC_LOCAL:0:6}... (${#SEC_LOCAL} char)"
if [ -n "$SEC_NGINX" ] && [ "$SEC_NGINX" = "$SEC_LOCAL" ]; then
    ok "COCOK"
else
    gagal "TIDAK COCOK → /cache/files/... akan SELALU 403"
    info "FIX: bash scripts/perbaiki_oo.sh"
fi

# ── 3. JWT sama (container vs .env)? ──────────────────────────────────
judul "3. JWT (editor mati diam-diam kalau beda)"
if [ -f "$(dirname "$0")/jalankan_oo.sh" ]; then
    bash "$(dirname "$0")/jalankan_oo.sh" --status 2>&1 | grep -E "COCOK|TIDAK|panjang|runtime|\.env" | head -5
else
    info "skrip jalankan_oo.sh tidak ditemukan — lewati"
fi

# ── 4. WebSocket diterima? ────────────────────────────────────────────
judul "4. WebSocket (socket.io)"
WS_TOLAK=$(docker logs "$APP" --since 5m 2>&1 | grep -c "oo-aset-ws] ditolak" || true)
WS_OK=$(docker logs "$APP" --since 5m 2>&1 | grep -c "oo-aset-ws] \[accepted\]" || true)
info "ditolak: $WS_TOLAK | accepted: $WS_OK"
if [ "$WS_OK" -gt 0 ]; then
    ok "WebSocket diterima"
elif [ "$WS_TOLAK" -gt 0 ]; then
    gagal "WebSocket DITOLAK — cek nama cookie (harus SESSION_COOKIE)"
    docker logs "$APP" --since 5m 2>&1 | grep "oo-aset-ws] ditolak" | tail -2 | sed 's/^/    /'
else
    info "belum ada aktivitas WebSocket 5 menit terakhir"
fi

# ── 5. Request gagal 4xx? ─────────────────────────────────────────────
judul "5. Request gagal (5 menit terakhir)"
GAGAL=$(docker logs "$APP" --since 5m 2>&1 \
    | grep -oE '(GET|POST) [^ ]+ HTTP/1.1" 40[0-9]' | sort -u | head -8)
if [ -z "$GAGAL" ]; then
    ok "tidak ada 4xx"
else
    printf '%s\n' "$GAGAL" | sed 's/^/  /'
    case "$GAGAL" in
        */cache/files/*) info "→ prefix /oo/aset HILANG? cek X-Forwarded-Prefix di app/main.py" ;;
    esac
fi

# ── 6. X-Forwarded di app? ────────────────────────────────────────────
judul "6. Header X-Forwarded (app/main.py)"
SISA=$(dirname "$0")/../app/main.py
if [ -f "$SISA" ]; then
    # Hitung KODE saja (pola "X-Forwarded-X': '...'"), bukan komentar.
    N_PROTO=$(grep -c "'X-Forwarded-Proto':" "$SISA" || true)
    N_PREFIX=$(grep -c "'X-Forwarded-Prefix':" "$SISA" || true)
    [ "$N_PROTO" = "2" ] && ok "X-Forwarded-Proto di 2 tempat" \
                         || gagal "X-Forwarded-Proto: $N_PROTO (harus 2)"
    [ "$N_PREFIX" = "2" ] && ok "X-Forwarded-Prefix di 2 tempat" \
                          || gagal "X-Forwarded-Prefix: $N_PREFIX (harus 2)"
else
    info "app/main.py tidak ditemukan dari $SISA"
fi

echo
echo "${TEBAL}Selesai.${NORMAL} Kalau ada ✗ → jalankan: ${TEBAL}bash scripts/perbaiki_oo.sh${NORMAL}"
echo
