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
#  PERBAIKI OO — pulihkan setelan OnlyOffice setelah container dibuat ulang
# ═══════════════════════════════════════════════════════════════════════
#
#  KENAPA SKRIP INI ADA
#  ─────────────────────
#  Container `oo-converter` dijalankan dari image resmi OnlyOffice. Image
#  itu MENIMPA konfigurasi di dalam container setiap kali container dibuat
#  ulang. Akibatnya, semua perbaikan ini HILANG:
#
#    1. Header CORS      -> tanpa ini, browser BLOKIR pemuatan editor
#                           (OnlyOffice tidak kirim Access-Control-Allow-Origin)
#    2. Tutup /welcome   -> tanpa ini, halaman admin OnlyOffice terbuka publik
#    3. Header WebSocket -> tanpa ini, kolaborasi real-time gagal (405)
#    4. JWT secret       -> harus SAMA dengan yang di .env aplikasi kita,
#                           kalau tidak editor gagal tanda tangan
#
#  CARA PAKAI
#  ──────────
#    bash scripts/perbaiki_oo.sh            # perbaiki + verifikasi
#    bash scripts/perbaiki_oo.sh --cek      # hanya periksa, tidak mengubah
#
#  Aman dijalankan berkali-kali (idempoten).
# ═══════════════════════════════════════════════════════════════════════
set -uo pipefail

CT="oo-converter"
APP="eduai-app"
ENV_FILE="$(dirname "$0")/../.env"
MODE="${1:-perbaiki}"

HIJAU=$'\033[0;32m'; MERAH=$'\033[0;31m'; KUNING=$'\033[0;33m'
BIRU=$'\033[0;34m'; TEBAL=$'\033[1m'; NORMAL=$'\033[0m'

ok()   { echo "  ${HIJAU}✓${NORMAL} $*"; }
gagal(){ echo "  ${MERAH}✗${NORMAL} $*"; }
info() { echo "  ${BIRU}→${NORMAL} $*"; }
judul(){ echo; echo "${TEBAL}${BIRU}═══ $* ═══${NORMAL}"; }

ADA_MASALAH=0

# ── 0. Cek container hidup ────────────────────────────────────────────
judul "0. Cek container"

if ! docker ps --format '{{.Names}}' | grep -qx "$CT"; then
    gagal "Container '$CT' TIDAK JALAN"
    echo
    echo "  Buat ulang dengan:"
    echo "    docker run -d --name $CT --network bridge \\"
    echo "      -p 127.0.0.1:18081:80 onlyoffice/documentserver:latest"
    exit 1
fi
ok "Container '$CT' jalan"
IP_OO=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$CT")
info "IP internal: $IP_OO"

if ! docker ps --format '{{.Names}}' | grep -qx "$APP"; then
    gagal "Container '$APP' TIDAK JALAN"
    ADA_MASALAH=1
else
    ok "Container '$APP' jalan"
fi

# ── 1. Header CORS ────────────────────────────────────────────────────
judul "1. Header CORS (wajib — tanpa ini editor DIBLOKIR browser)"

if docker exec "$CT" grep -q 'Access-Control-Allow-Origin' \
        /etc/nginx/includes/eduai-cors.conf 2>/dev/null; then
    ok "eduai-cors.conf sudah ada"
else
    if [ "$MODE" = "--cek" ]; then
        gagal "eduai-cors.conf HILANG"
        ADA_MASALAH=1
    else
        info "membuat eduai-cors.conf..."
        # 'more_set_headers' dipakai karena 'add_header' di dalam 'location'
        # MENGGANTIKAN header level server (modul headers-more tersedia).
        docker exec "$CT" sh -c "cat > /etc/nginx/includes/eduai-cors.conf <<'EOF'
# ── CORS untuk EduAi Publishing ──────────────────────────────────
# OnlyOffice tidak mengirim header CORS. Karena 'add_header' di dalam
# 'location' MENGGANTIKAN header level server, dipakai 'more_set_headers'.
more_set_headers 'Access-Control-Allow-Origin: https://eduai.bikinaja.id' always;
more_set_headers 'Access-Control-Allow-Credentials: true' always;
more_set_headers 'Access-Control-Allow-Methods: GET, POST, OPTIONS' always;
more_set_headers 'Access-Control-Allow-Headers: Content-Type, Authorization, Accept, Origin, X-Requested-With' always;
more_set_headers 'Access-Control-Expose-Headers: Content-Length, Content-Range' always;

location = /eduai-preflight {
    more_set_headers 'Access-Control-Allow-Origin: https://eduai.bikinaja.id' always;
    more_set_headers 'Access-Control-Allow-Credentials: true' always;
    more_set_headers 'Access-Control-Allow-Methods: GET, POST, OPTIONS' always;
    more_set_headers 'Access-Control-Allow-Headers: Content-Type, Authorization, Accept, Origin, X-Requested-With' always;
    more_set_headers 'Content-Length: 0' always;
    more_set_headers 'Content-Type: text/plain' always;
    return 204;
}
EOF"
        ok "eduai-cors.conf dibuat"
    fi
fi

# ── 2. Tutup endpoint internal ────────────────────────────────────────
judul "2. Tutup endpoint internal (admin/info dari publik)"

if docker exec "$CT" test -f /etc/nginx/includes/eduai-tutup.conf 2>/dev/null; then
    ok "eduai-tutup.conf sudah ada"
else
    if [ "$MODE" = "--cek" ]; then
        gagal "eduai-tutup.conf HILANG"
        ADA_MASALAH=1
    else
        info "membuat eduai-tutup.conf..."
        docker exec "$CT" sh -c "cat > /etc/nginx/includes/eduai-tutup.conf <<'EOF'
# ── TUTUP endpoint internal OnlyOffice dari publik ────────────────
# Hanya izinkan yang DIBUTUHKAN editor. Sisanya ditolak.
location ~* ^/(welcome|example|info|metrics|adminpanel|index\.html)(/|$) {
    return 403;
}
location = /healthcheck {
    return 403;
}
location ~* ^/(info|HealthCheck)(/|$) {
    return 403;
}
EOF"
        ok "eduai-tutup.conf dibuat"
    fi
fi

# ── 3. Sertakan kedua file di ds.conf ─────────────────────────────────
judul "3. Aktifkan include di ds.conf"

if docker exec "$CT" grep -q 'eduai-cors' /etc/nginx/conf.d/ds.conf 2>/dev/null \
   && docker exec "$CT" grep -q 'eduai-tutup' /etc/nginx/conf.d/ds.conf 2>/dev/null; then
    ok "ds.conf sudah menyertakan cors + tutup"
else
    if [ "$MODE" = "--cek" ]; then
        gagal "ds.conf BELUM menyertakan eduai-cors/eduai-tutup"
        ADA_MASALAH=1
    else
        info "menyisipkan include ke ds.conf..."
        docker exec "$CT" sh -c "
cp /etc/nginx/conf.d/ds.conf /etc/nginx/conf.d/ds.conf.bak.\$(date +%s)
sed -i 's#include /etc/nginx/includes/ds-\*.conf;#include /etc/nginx/includes/eduai-cors.conf;\n  include /etc/nginx/includes/eduai-tutup.conf;\n  include /etc/nginx/includes/ds-*.conf;#' /etc/nginx/conf.d/ds.conf
"
        ok "ds.conf diperbarui"
    fi
fi

# ── 4. Header WebSocket ───────────────────────────────────────────────
judul "4. Header WebSocket (kolaborasi real-time, cegah galat 405)"

DS_DOC="/etc/nginx/includes/ds-docservice.conf"
if docker exec "$CT" grep -q 'proxy_set_header Upgrade' "$DS_DOC" 2>/dev/null; then
    ok "header WebSocket sudah ada di ds-docservice.conf"
else
    if [ "$MODE" = "--cek" ]; then
        gagal "header WebSocket HILANG di ds-docservice.conf"
        ADA_MASALAH=1
    else
        info "menambahkan header WebSocket..."
        docker exec "$CT" sh -c "cp $DS_DOC /tmp/ds-docservice.conf.bak.\$(date +%s)"
        # Tulis skrip Python ke file DULU (hindari masalah quoting heredoc),
        # lalu jalankan di dalam container.
        TMP_PY=$(mktemp)
        cat > "$TMP_PY" <<'PYEOF'
import re

p = '/etc/nginx/includes/ds-docservice.conf'
s = open(p).read()

if 'proxy_set_header Upgrade' in s:
    print('  sudah ada')
else:
    ws_blok = ('\n  # ── WebSocket untuk socket.io (kolaborasi real-time) ──────────\n'
               '  # Tanpa header ini socket.io gagal 405 dan kolaborasi mati.\n'
               '  proxy_set_header Upgrade $http_upgrade;\n'
               '  proxy_set_header Connection "upgrade";\n')

    # Cari 'location / {' yang diikuti proxy_pass http://docservice
    m = re.search(r'(location / \{\s*\n\s*proxy_pass http://docservice;'
                  r'\s*\n\s*proxy_http_version 1\.1;)', s)
    if m:
        sisip = m.group(1) + ws_blok
        s2 = s[:m.start(1)] + sisip + s[m.end(1):]
        open(p, 'w').write(s2)
        print('  ✓ header WebSocket disisipkan')
    else:
        print('  ⚠️ pola location / tidak ketemu — tambah manual:')
        print('     proxy_set_header Upgrade $http_upgrade;')
        print('     proxy_set_header Connection "upgrade";')
PYEOF
        docker cp "$TMP_PY" "$CT:/tmp/tambah_ws.py" >/dev/null
        docker exec "$CT" python3 /tmp/tambah_ws.py
        rm -f "$TMP_PY"
        ok "header WebSocket diproses"
    fi
fi

# ── 5. disable_cors ───────────────────────────────────────────────────
judul "5. disable_cors (socket.io)"

if docker exec "$CT" grep -q '"disable_cors": false' \
        /etc/onlyoffice/documentserver/default.json 2>/dev/null; then
    ok "disable_cors sudah false"
else
    if [ "$MODE" = "--cek" ]; then
        gagal "disable_cors masih true"
        ADA_MASALAH=1
    else
        info "mengubah disable_cors -> false..."
        docker exec "$CT" sh -c "
F=/etc/onlyoffice/documentserver/default.json
cp \$F \${F}.bak.\$(date +%s)
sed -i 's/\"disable_cors\": true/\"disable_cors\": false/' \$F
"
        ok "disable_cors diubah"
    fi
fi

# ── 6. JWT secret — samakan dengan .env aplikasi ──────────────────────
judul "6. JWT secret (harus SAMA dengan .env aplikasi)"

SECRET_RUNTIME=$(docker exec "$CT" python3 -c "
import json
print(json.load(open('/etc/onlyoffice/documentserver/local.json'))
      ['services']['CoAuthoring']['secret']['browser']['string'])
" 2>/dev/null || echo "")

SECRET_ENV=""
if [ -f "$ENV_FILE" ]; then
    SECRET_ENV=$(grep -E '^EDUAI_OO_JWT_SECRET=' "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'")
fi

if [ -z "$SECRET_RUNTIME" ]; then
    gagal "secret runtime tidak terbaca"
    ADA_MASALAH=1
elif [ -z "$SECRET_ENV" ]; then
    info "secret di .env kosong — menuliskan dari container..."
    if [ "$MODE" != "--cek" ]; then
        echo "EDUAI_OO_JWT_SECRET=$SECRET_RUNTIME" >> "$ENV_FILE"
        chmod 600 "$ENV_FILE"
        ok "secret ditulis ke .env"
    fi
elif [ "$SECRET_RUNTIME" = "$SECRET_ENV" ]; then
    ok "secret COCOK (panjang ${#SECRET_RUNTIME})"
else
    gagal "secret TIDAK COCOK — editor akan gagal tanda tangan!"
    info "runtime : ${SECRET_RUNTIME:0:8}... (${#SECRET_RUNTIME} char)"
    info ".env    : ${SECRET_ENV:0:8}... (${#SECRET_ENV} char)"
    if [ "$MODE" != "--cek" ]; then
        # Percayai RUNTIME (yang dipakai OnlyOffice saat ini), tulis ke .env
        /opt/data/.venv/bin/python3 - "$SECRET_RUNTIME" "$ENV_FILE" <<'PYEOF'
import re, sys
sec, fn = sys.argv[1], sys.argv[2]
s = open(fn).read()
if re.search(r'^EDUAI_OO_JWT_SECRET=', s, re.M):
    s = re.sub(r'^EDUAI_OO_JWT_SECRET=.*$',
               f'EDUAI_OO_JWT_SECRET={sec}', s, flags=re.M)
else:
    s += f'\nEDUAI_OO_JWT_SECRET={sec}\n'
open(fn, 'w').write(s)
print('  .env disamakan dengan runtime')
PYEOF
        chmod 600 "$ENV_FILE"
        info "jalankan ulang: bash scripts/jalankan.sh"
    fi
    ADA_MASALAH=1
fi

# ── 6b. SECURE LINK — dua secret HARUS sama (bug 12Sep26) ─────────────
# OnlyOffice menghitung md5 URL /cache/files/... pakai
#   storage.fs.secretString  (local.json)
# nginx MEMVERIFIKASI pakai
#   $secure_link_secret      (ds.conf)
#
# Kalau BEDA -> SELALU 403 -> Editor.bin tidak bisa diambil -> dokumen
# TIDAK PERNAH TERMUAT ("no logic document", canvas kosong).
#
# JEBAKAN: skrip resmi documentserver-update-securelink.sh menulis ke
# /etc/onlyoffice/documentserver/nginx/ds.conf (TEMPLATE), padahal nginx
# membaca /etc/nginx/conf.d/ds.conf (AKTIF). Skrip resmi TIDAK EFEKTIF.
judul "6b. Secure link (secret md5 Editor.bin)"

DS_AKTIF=/etc/nginx/conf.d/ds.conf
SEC_NGINX=$(docker exec "$CT" sh -c \
    "grep -oP 'secure_link_secret \\K[A-Za-z0-9]+' $DS_AKTIF 2>/dev/null" 2>/dev/null)
SEC_LOCAL=$(docker exec "$CT" sh -c \
    "grep -oP 'secretString\"\\s*:\\s*\"\\K[^\"]+' /etc/onlyoffice/documentserver/local.json 2>/dev/null" 2>/dev/null)

if [ -z "$SEC_NGINX" ] || [ -z "$SEC_LOCAL" ]; then
    gagal "secret secure_link tidak terbaca (nginx='$SEC_NGINX' local='$SEC_LOCAL')"
    ADA_MASALAH=1
elif [ "$SEC_NGINX" = "$SEC_LOCAL" ]; then
    ok "secret COCOK (${#SEC_NGINX} char)"
else
    gagal "secret TIDAK COCOK — /cache/files/... akan SELALU 403!"
    info "nginx ds.conf : ${SEC_NGINX:0:6}..."
    info "local.json    : ${SEC_LOCAL:0:6}..."
    if [ "$MODE" != "--cek" ]; then
        info "menyamakan ke nilai local.json (yang dipakai docservice)..."
        docker exec "$CT" sh -c \
            "sed -i 's|set \$secure_link_secret .*|set \$secure_link_secret ${SEC_LOCAL};|' $DS_AKTIF" \
            && ok "ds.conf aktif disamakan"
        BARU=$(docker exec "$CT" sh -c \
            "grep -oP 'secure_link_secret \\K[A-Za-z0-9]+' $DS_AKTIF" 2>/dev/null)
        [ "$BARU" = "$SEC_LOCAL" ] && ok "verifikasi: sekarang COCOK" \
                                   || gagal "verifikasi gagal ($BARU)"
    fi
    ADA_MASALAH=1
fi

# ── 7. Muat ulang nginx + verifikasi ──────────────────────────────────
judul "7. Muat ulang nginx + verifikasi"

if [ "$MODE" != "--cek" ]; then
    if docker exec "$CT" nginx -t 2>&1 | grep -q 'test is successful'; then
        docker exec "$CT" nginx -s reload >/dev/null 2>&1
        ok "nginx dimuat ulang"
    else
        gagal "konfigurasi nginx TIDAK SAH — perubahan dibatalkan"
        docker exec "$CT" nginx -t 2>&1 | tail -3
        ADA_MASALAH=1
    fi
fi

sleep 2

printf "  %-34s" "CORS"
docker exec "$CT" sh -c "curl -s -D - -o /dev/null -H 'Origin: https://eduai.bikinaja.id' \
    http://127.0.0.1/web-apps/apps/api/documents/api.js" 2>/dev/null \
    | grep -qi 'access-control-allow-origin' \
    && echo "${HIJAU}✓ aktif${NORMAL}" || { echo "${MERAH}✗ mati${NORMAL}"; ADA_MASALAH=1; }

printf "  %-34s" "/welcome (harus 403)"
W=$(docker exec "$CT" sh -c "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/welcome/" 2>/dev/null)
[ "$W" = "403" ] && echo "${HIJAU}✓ $W${NORMAL}" || { echo "${MERAH}✗ $W${NORMAL}"; ADA_MASALAH=1; }

printf "  %-34s" "api.js (harus 200)"
A=$(docker exec "$CT" sh -c "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/web-apps/apps/api/documents/api.js" 2>/dev/null)
[ "$A" = "200" ] && echo "${HIJAU}✓ $A${NORMAL}" || { echo "${MERAH}✗ $A${NORMAL}"; ADA_MASALAH=1; }

printf "  %-34s" "WebSocket header"
docker exec "$CT" grep -q 'proxy_set_header Upgrade' "$DS_DOC" 2>/dev/null \
    && echo "${HIJAU}✓ ada${NORMAL}" || { echo "${MERAH}✗ tidak ada${NORMAL}"; ADA_MASALAH=1; }

printf "  %-34s" "Aset editor (harus 303)"
if docker ps --format '{{.Names}}' | grep -qx "$APP"; then
    K=$(docker exec "$CT" sh -c "curl -s -o /dev/null -w '%{http_code}' \
        http://$IP_OO:80/healthcheck" 2>/dev/null)
    APP_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$APP" 2>/dev/null)
    R=$(docker exec "$CT" sh -c "curl -s -o /dev/null -w '%{http_code}' \
        http://$APP_IP:8000/oo/aset/web-apps/apps/api/documents/api.js" 2>/dev/null)
    [ "$R" = "303" ] && echo "${HIJAU}✓ $R (wajib login)${NORMAL}" \
                     || echo "${KUNING}? $R${NORMAL}"
fi

# ── 8. REBRANDING EduAi (logo + About) ────────────────────────────────
judul "8. Rebranding EduAi (logo header + About)"

# Semua perubahan branding ada di FILE DI DALAM container OO, jadi ikut
# hilang saat container dibuat ulang. Tiga skrip di bawah memasangnya
# kembali (idempoten — aman dijalankan berulang).
DIR_SKRIP="$(cd "$(dirname "$0")" && pwd)"
PY="python3"

if [ "$MODE" = "--cek" ]; then
    # mode cek: hanya laporkan status
    printf "  %-34s" "Logo header biru"
    if docker exec "$CT" grep -q 'EduAi' \
        /var/www/onlyoffice/documentserver/web-apps/apps/common/main/resources/img/header/dark-logo_s.svg 2>/dev/null \
        || docker exec "$CT" test -s \
        /var/www/onlyoffice/documentserver/web-apps/apps/common/main/resources/img/header/dark-logo_s.svg; then
        SZ=$(docker exec "$CT" sh -c 'stat -c %s /var/www/onlyoffice/documentserver/web-apps/apps/common/main/resources/img/header/dark-logo_s.svg' 2>/dev/null)
        if [ "$SZ" -gt 20000 ] 2>/dev/null; then
            echo "${HIJAU}✓ terpasang (${SZ} B)${NORMAL}"
        else
            echo "${MERAH}✗ masih bawaan (${SZ} B)${NORMAL}"
            ADA_MASALAH=1
        fi
    else
        echo "${MERAH}✗ tidak ada${NORMAL}"
        ADA_MASALAH=1
    fi

    printf "  %-34s" "Data About (About.js)"
    docker exec "$CT" grep -q 'EduAi INOVASI' \
        /var/www/onlyoffice/documentserver/web-apps/apps/common/main/lib/view/About.js 2>/dev/null \
        && echo "${HIJAU}✓ ada${NORMAL}" \
        || { echo "${MERAH}✗ tidak ada${NORMAL}"; ADA_MASALAH=1; }

    printf "  %-34s" "Logo About (CSS fix)"
    N=$(docker exec "$CT" sh -c "grep -l 'EDUAI-ABOUT-FIX' \
        /var/www/onlyoffice/documentserver/web-apps/apps/*/main/resources/css/app.css 2>/dev/null | wc -l")
    if [ "$N" -ge 5 ]; then
        echo "${HIJAU}✓ $N/5 editor${NORMAL}"
    else
        echo "${MERAH}✗ hanya $N/5${NORMAL}"
        ADA_MASALAH=1
    fi

    printf "  %-34s" "File logo About"
    docker exec "$CT" test -s \
        /var/www/onlyoffice/documentserver/web-apps/apps/common/main/resources/img/about/logo-eduai-about.png 2>/dev/null \
        && echo "${HIJAU}✓ ada${NORMAL}" \
        || { echo "${MERAH}✗ tidak ada${NORMAL}"; ADA_MASALAH=1; }

    printf "  %-34s" "Warna tab Kolaborasi"
    N_TAB=$(docker exec "$CT" sh -c "grep -l 'EDUAI-TAB-COLLAB' /var/www/onlyoffice/documentserver/web-apps/apps/*/main/resources/css/app.css 2>/dev/null | wc -l")
    if [ "${N_TAB:-0}" -ge 5 ]; then
        echo "${HIJAU}✓ $N_TAB/5 editor${NORMAL}"
    else
        echo "${MERAH}✗ hanya ${N_TAB:-0}/5${NORMAL}"; ADA_MASALAH=1
    fi

    printf "  %-34s" "Tab AI (config plugin)"
    if docker exec "$CT" python3 -c "
import json,sys
d=json.load(open('/var/www/onlyoffice/documentserver/sdkjs-plugins/{9DC93CDB-B576-4F0C-B55E-FCC9C48DD007}/config.json'))
sys.exit(0 if (d.get('tab') or {}).get('id')=='eduai-ai' else 1)
" 2>/dev/null; then
        echo "${HIJAU}✓ terpasang${NORMAL}"
    else
        echo "${MERAH}✗ belum${NORMAL}"; ADA_MASALAH=1
    fi
else
    # mode perbaiki: jalankan ketiga skrip pasang
    for TAHAP in "buat_logo_header.py:logo header" \
                 "ganti_logo_header.py:pasang logo header" \
                 "rebrand_about.py:data About.js" \
                 "rebrand_about2.py:label About.js" \
                 "perbaiki_logo_about.py:logo About (CSS)" \
                 "perbaiki_tab_ai.py:tab AI (config plugin)" \
                 "perbaiki_tab_kolaborasi.py:warna tab Kolaborasi+AI"; do
        SKRIP="${TAHAP%%:*}"
        LABEL="${TAHAP#*:}"
        if [ -f "$DIR_SKRIP/$SKRIP" ]; then
            printf "  %-34s" "$LABEL"
            if OUT=$("$PY" "$DIR_SKRIP/$SKRIP" 2>&1); then
                echo "${HIJAU}✓${NORMAL}"
            else
                echo "${MERAH}✗${NORMAL}"
                echo "$OUT" | tail -3 | sed 's/^/      /'
                ADA_MASALAH=1
            fi
        else
            printf "  %-34s${MERAH}✗ skrip tidak ada${NORMAL}\n" "$LABEL"
            ADA_MASALAH=1
        fi
    done

    # ── FLUSH CACHE OO ───────────────────────────────────────────────
    #  WAJIB: aset OO diserve lewat path ber-versi 9.4.0-<cache_tag> dan
    #  di-cache browser/CF. Kalau cache_tag TIDAK diubah, browser tetap
    #  pakai app.css LAMA (tab Kolaborasi tetap putih walau file di
    #  server sudah benar). documentserver-flush-cache.sh = skrip RESMI
    #  OO yang menulis ulang ds-cache.conf dengan hash baru.
    printf "  %-34s" "Flush cache aset OO"
    TAG_LAMA=$(docker exec "$CT" sh -c "grep -o '\"[a-f0-9]\{32\}\"' /etc/nginx/includes/ds-cache.conf 2>/dev/null" || echo "")
    if docker exec "$CT" bash /usr/bin/documentserver-flush-cache.sh >/dev/null 2>&1; then
        TAG_BARU=$(docker exec "$CT" sh -c "grep -o '\"[a-f0-9]\{32\}\"' /etc/nginx/includes/ds-cache.conf 2>/dev/null" || echo "")
        if [ "$TAG_LAMA" != "$TAG_BARU" ]; then
            echo "${HIJAU}✓${NORMAL} tag berubah"
        else
            echo "${HIJAU}✓${NORMAL}"
        fi
    else
        echo "${KUNING}?${NORMAL} dilewati"
    fi
fi

# ── Ringkasan ─────────────────────────────────────────────────────────
judul "RINGKASAN"
if [ "$ADA_MASALAH" -eq 0 ]; then
    echo "  ${HIJAU}${TEBAL}SEMUA SETELAN AMAN ✓${NORMAL}"
    echo
    echo "  Editor OnlyOffice siap dipakai."
    if [ "$MODE" != "--cek" ]; then
        echo
        echo "  ${KUNING}${TEBAL}PENTING:${NORMAL} purge cache Cloudflare supaya"
        echo "  perubahan branding langsung terlihat user:"
        echo "    python3 scripts/purge_cf_aset.py"
    fi
else
    echo "  ${MERAH}${TEBAL}ADA MASALAH YANG BELUM BERES ✗${NORMAL}"
    echo
    echo "  Jalankan tanpa --cek untuk memperbaiki:"
    echo "    bash scripts/perbaiki_oo.sh"
    exit 1
fi
echo
