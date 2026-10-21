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
#  UJI KETAHANAN PONDASI — simulasi berbagai bencana
# ═══════════════════════════════════════════════════════════════════════
#  Menguji apakah pondasi EduAi Publishing tahan terhadap:
#    B1. nginx dimuat ulang (reload)
#    B2. container oo-converter di-restart
#    B3. container dihapus + dibuat ulang (docker rm + run)
#    B4. aplikasi eduai-app di-restart
#    B5. aplikasi dihapus + dibuat ulang
#    B6. SEMUA container mati (simulasi reboot server)
#
#  Cara pakai: bash scripts/uji_bencana.sh [B1|B2|...]
# ═══════════════════════════════════════════════════════════════════════
set -uo pipefail

CT=oo-converter
APP=eduai-app
IP_OO=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $CT 2>/dev/null)
IP_APP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $APP 2>/dev/null)

H=$'\033[0;32m'; M=$'\033[0;31m'; K=$'\033[0;33m'; B=$'\033[0;34m'; T=$'\033[1m'; N=$'\033[0m'

# ── Fungsi pemeriksa ──────────────────────────────────────────────────
periksa() {
    local lulus=0 total=0

    # 1. CORS
    total=$((total+1))
    if docker exec $CT sh -c "curl -s -D - -o /dev/null \
        -H 'Origin: https://eduai.bikinaja.id' \
        http://127.0.0.1/web-apps/apps/api/documents/api.js" 2>/dev/null \
        | grep -qi 'access-control-allow-origin'; then
        printf "    CORS                      ${H}✓${N}\n"; lulus=$((lulus+1))
    else
        printf "    CORS                      ${M}✗${N}\n"
    fi

    # 2. /welcome ditutup
    total=$((total+1))
    local w=$(docker exec $CT sh -c "curl -s -o /dev/null -w '%{http_code}' \
        http://127.0.0.1/welcome/" 2>/dev/null)
    if [ "$w" = "403" ]; then
        printf "    /welcome tertutup         ${H}✓${N}\n"; lulus=$((lulus+1))
    else
        printf "    /welcome tertutup         ${M}✗ ($w)${N}\n"
    fi

    # 3. api.js hidup
    total=$((total+1))
    local a=$(docker exec $CT sh -c "curl -s -o /dev/null -w '%{http_code}' \
        http://127.0.0.1/web-apps/apps/api/documents/api.js" 2>/dev/null)
    if [ "$a" = "200" ]; then
        printf "    api.js hidup              ${H}✓${N}\n"; lulus=$((lulus+1))
    else
        printf "    api.js hidup              ${M}✗ ($a)${N}\n"
    fi

    # 4. Header WebSocket
    total=$((total+1))
    if docker exec $CT grep -q 'proxy_set_header Upgrade' \
        /etc/nginx/includes/ds-docservice.conf 2>/dev/null; then
        printf "    header WebSocket          ${H}✓${N}\n"; lulus=$((lulus+1))
    else
        printf "    header WebSocket          ${M}✗${N}\n"
    fi

    # 5. JWT secret cocok
    total=$((total+1))
    local sr=$(docker exec $CT python3 -c "
import json
print(json.load(open('/etc/onlyoffice/documentserver/local.json'))
      ['services']['CoAuthoring']['secret']['browser']['string'])" 2>/dev/null)
    local se=$(grep -E '^EDUAI_OO_JWT_SECRET=' \
        "$(dirname "$0")/../.env" | cut -d= -f2- | tr -d '"'"'"'')
    if [ -n "$sr" ] && [ "$sr" = "$se" ]; then
        printf "    JWT secret cocok          ${H}✓${N}\n"; lulus=$((lulus+1))
    else
        printf "    JWT secret cocok          ${M}✗ (ganti!)${N}\n"
    fi

    # 6. App sehat + aset terlindungi
    total=$((total+1))
    if docker ps --format '{{.Names}}' | grep -qx $APP; then
        local ipx=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $APP 2>/dev/null)
        local r=$(docker exec $CT sh -c "curl -s -o /dev/null -w '%{http_code}' \
            http://$ipx:8000/oo/aset/web-apps/apps/api/documents/api.js" 2>/dev/null)
        if [ "$r" = "303" ]; then
            printf "    aset wajib login (303)    ${H}✓${N}\n"; lulus=$((lulus+1))
        else
            printf "    aset wajib login (303)    ${M}✗ ($r)${N}\n"
        fi
    else
        printf "    app hidup                 ${M}✗ (mati)${N}\n"
    fi

    echo
    if [ "$lulus" -eq "$total" ]; then
        echo "    ${T}${H}HASIL: $lulus/$total TAHAN ✓${N}"
    else
        echo "    ${T}${M}HASIL: $lulus/$total — ADA YANG RAPUH ✗${N}"
    fi
    return $((total - lulus))
}

banner() {
    echo
    echo "${T}${B}╔══════════════════════════════════════════════════════════╗${N}"
    echo "${T}${B}║  $1${N}"
    echo "${T}${B}╚══════════════════════════════════════════════════════════╝${N}"
}

# ═════════════════════════════════════════════════════════════════════
# B0. Kondisi awal
# ═════════════════════════════════════════════════════════════════════
banner "B0. KONDISI AWAL (sebelum bencana)"
periksa
AWAL=$?

SKENARIO="${1:-semua}"

# ═════════════════════════════════════════════════════════════════════
# B1. nginx reload
# ═════════════════════════════════════════════════════════════════════
if [ "$SKENARIO" = "semua" ] || [ "$SKENARIO" = "B1" ]; then
    banner "B1. BENCANA: nginx dimuat ulang"
    docker exec $CT nginx -s reload >/dev/null 2>&1
    sleep 3
    periksa
fi

# ═════════════════════════════════════════════════════════════════════
# B2. restart container oo-converter
# ═════════════════════════════════════════════════════════════════════
if [ "$SKENARIO" = "semua" ] || [ "$SKENARIO" = "B2" ]; then
    banner "B2. BENCANA: container oo-converter di-restart"
    docker restart $CT >/dev/null 2>&1
    echo "    menunggu container siap..."
    for i in $(seq 1 30); do
        sleep 2
        docker exec $CT sh -c "curl -s -o /dev/null http://127.0.0.1/web-apps/apps/api/documents/api.js" 2>/dev/null && break
    done
    sleep 3
    IP_OO=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $CT 2>/dev/null)
    echo "    IP baru: $IP_OO"
    periksa
fi

# ═════════════════════════════════════════════════════════════════════
# B3. hapus + buat ulang container (bencana terberat untuk oo-converter)
# ═════════════════════════════════════════════════════════════════════
if [ "$SKENARIO" = "semua" ] || [ "$SKENARIO" = "B3" ]; then
    banner "B3. BENCANA: oo-converter DIHAPUS & DIBUAT ULANG"
    docker stop $CT >/dev/null 2>&1
    docker rm $CT >/dev/null 2>&1
    echo "    container dihapus"

    # Cara buat ulang harus SAMA seperti aslinya (volume dipertahankan)
    bash "$(dirname "$0")/jalankan_oo.sh" 2>/dev/null || \
    docker run -d --name $CT --network bridge \
        -v onlyoffice_data:/var/www/onlyoffice/Data \
        -v onlyoffice_fonts:/usr/share/fonts/truetype/custom \
        -v onlyoffice_lib:/var/lib/onlyoffice \
        -v onlyoffice_logs:/var/log/onlyoffice \
        onlyoffice/documentserver:latest >/dev/null 2>&1

    echo "    menunggu siap..."
    for i in $(seq 1 40); do
        sleep 3
        docker exec $CT sh -c "curl -s -o /dev/null http://127.0.0.1/web-apps/apps/api/documents/api.js" 2>/dev/null && break
    done
    sleep 4
    IP_OO=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $CT 2>/dev/null)
    echo "    IP baru: $IP_OO"
    echo
    echo "    ${K}--- TANPA perbaikan (kondisi apa adanya) ---${N}"
    periksa
    echo
    echo "    ${K}--- SETELAH jalankan perbaiki_oo.sh ---${N}"
    bash "$(dirname "$0")/perbaiki_oo.sh" >/tmp/perbaikan.log 2>&1
    bash "$(dirname "$0")/jalankan.sh" >/dev/null 2>&1
    sleep 14
    periksa
fi

# ═════════════════════════════════════════════════════════════════════
# B4. restart aplikasi
# ═════════════════════════════════════════════════════════════════════
if [ "$SKENARIO" = "semua" ] || [ "$SKENARIO" = "B4" ]; then
    banner "B4. BENCANA: aplikasi eduai-app di-restart"
    docker restart $APP >/dev/null 2>&1
    sleep 14
    periksa
fi

# ═════════════════════════════════════════════════════════════════════
# B5. hapus + buat ulang aplikasi
# ═════════════════════════════════════════════════════════════════════
if [ "$SKENARIO" = "semua" ] || [ "$SKENARIO" = "B5" ]; then
    banner "B5. BENCANA: aplikasi DIHAPUS & DIBUAT ULANG"
    docker stop $APP >/dev/null 2>&1
    docker rm $APP >/dev/null 2>&1
    echo "    aplikasi dihapus"
    bash "$(dirname "$0")/jalankan.sh" >/dev/null 2>&1
    sleep 14
    periksa
fi

# ═════════════════════════════════════════════════════════════════════
# B6. SEMUA mati (simulasi reboot server)
# ═════════════════════════════════════════════════════════════════════
if [ "$SKENARIO" = "semua" ] || [ "$SKENARIO" = "B6" ]; then
    banner "B6. BENCANA: SEMUA container mati (simulasi reboot server)"
    docker stop $CT $APP >/dev/null 2>&1
    echo "    semua container dihentikan"
    echo "    (persis seperti server baru reboot — restart policy menentukan)"
    sleep 5

    # Cek restart policy (bukan 'docker stop' — itu stop manual, policy TIDAK berlaku)
    echo
    echo "    ${K}--- Restart policy (untuk crash, bukan stop manual) ---${N}"
    for c in oo-converter eduai-app; do
        RP=$(docker inspect $c --format '{{.HostConfig.RestartPolicy.Name}}' 2>/dev/null)
        if [ "$RP" = "unless-stopped" ] || [ "$RP" = "always" ]; then
            echo "    $c: ${H}$RP ✓${N} (hidup sendiri kalau CRASH)"
        else
            echo "    $c: ${M}$RP ✗${N} (TIDAK hidup sendiri)"
        fi
    done
    echo
    echo "    ${K}--- UJI NYATA: bunuh proses di dalam (simulasi crash) ---${N}"
    docker start $CT $APP >/dev/null 2>&1
    sleep 12
    RC_SEBELUM=$(docker inspect $CT --format '{{.RestartCount}}' 2>/dev/null)
    docker exec $CT sh -c "kill -9 \$(pgrep -f 'run-document-server' | head -1)" 2>/dev/null
    sleep 8
    S_OO=$(docker ps --filter name=$CT --format '{{.Status}}')
    case "$S_OO" in
      Up*) echo "    $CT: ${H}$S_OO ✓${N} — docker melindungi/hidupkan sendiri" ;;
      *)   echo "    $CT: ${M}$S_OO ✗${N} — TIDAK hidup sendiri" ;;
    esac
    echo
    echo "    ${K}--- Hidupkan manual (seperti yang harus dilakukan admin) ---${N}"
    docker start $CT $APP >/dev/null 2>&1
    sleep 20
    IP_OO=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $CT 2>/dev/null)
    IP_APP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $APP 2>/dev/null)
    echo "    IP oo: $IP_OO  |  IP app: $IP_APP"
    periksa
fi

banner "UJI KETAHANAN SELESAI"
