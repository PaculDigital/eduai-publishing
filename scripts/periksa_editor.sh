#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════
#  GERBANG EDITOR EDUAI — "editor hidup?" (dipasang 30Sep26)
# ══════════════════════════════════════════════════════════════════════════
#  KENAPA BERKAS INI ADA (akar terukur 30Sep26)
#
#  GEJALA: user buka dokumen -> modal "Editor melaporkan kesalahan:
#          {"errorCode":-4,"errorDescription":"Unduhan gagal."}"
#
#  AKAR: kunci `secure_link` BEDA antara
#     ds.conf    (nginx MEMVERIFIKASI)  -> sha8 976855b3
#     local.json (docservice MENGHITUNG) -> sha8 d81f1e85
#  `local.json` ditulis ULANG acak saat container OO boot (terukur
#  21 Sep 05:25:29, container start 05:25:10) sementara ds.conf masih
#  memegang kunci lama -> nginx SELALU 403 pada Editor.bin -> OO tidak
#  pernah dapat dokumen -> -4.
#
#  BUKTI SEBELUM/SESUDAH (terukur 30Sep26):
#     SEBELUM : Editor.bin 403 Forbidden  · 403 dlm 20 mnt = 1
#     SESUDAH : Editor.bin 200 OK         · 403 dlm 20 mnt = 0
#     alur    : GET /oo/unduh 200 · Editor.bin 200 · POST /oo/simpan 200
#
#  ⚠️ PAGAR LAMA (jalankan_oo.sh §5a) HANYA JALAN KALAU SKRIP ITU DIPANGGIL.
#     Kalau OO dibuat ulang dengan cara lain, rusak lagi TANPA SUARA.
#     Gerbang ini MENJAWAB langsung pertanyaan "editor hidup?" dari LUAR.
#
#  PAKAI:  bash scripts/periksa_editor.sh
#  KELUAR: 0 = editor hidup · 1 = ADA YANG RUSAK (jangan diamkan)
# ══════════════════════════════════════════════════════════════════════════
set -uo pipefail

PROYEK="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROYEK"

CT_OO="${EDUAI_CT_OO:-oo-converter}"
CT_APP="${EDUAI_CT_APP:-eduai-app}"
DOMAIN="${EDUAI_DOMAIN:-https://eduai.bikinaja.id}"

HIJAU=$'\033[0;32m'; MERAH=$'\033[0;31m'; KUNING=$'\033[0;33m'
BIRU=$'\033[0;34m'; TEBAL=$'\033[1m'; NORMAL=$'\033[0m'
ok()   { echo "  ${HIJAU}✓${NORMAL} $*"; }
bad()  { echo "  ${MERAH}✗${NORMAL} $*"; }
warn() { echo "  ${KUNING}!${NORMAL} $*"; }
info() { echo "  ${BIRU}→${NORMAL} $*"; }
judul(){ echo; echo "${TEBAL}${BIRU}═══ $* ═══${NORMAL}"; }

GAGAL=0
echo "${TEBAL}GERBANG EDITOR EDUAI${NORMAL} — $(date '+%d %b %Y %H:%M')"

# ── 0. Container hidup? ──────────────────────────────────────────────
judul "0. Container"
if docker ps --format '{{.Names}}' | grep -qx "$CT_OO"; then
    ok "$CT_OO jalan"
else
    bad "$CT_OO TIDAK jalan → editor pasti mati"
    GAGAL=1
fi
if docker ps --format '{{.Names}}' | grep -qx "$CT_APP"; then
    ok "$CT_APP jalan"
else
    bad "$CT_APP TIDAK jalan"
    GAGAL=1
fi
[ "$GAGAL" -ne 0 ] && { echo; echo "${MERAH}${TEBAL}⛔ GERBANG EDITOR GAGAL.${NORMAL}"; exit 1; }

# ── 1. KUNCI secure_link COCOK? (akar -4 terbukti) ───────────────────
judul "1. Kunci secure_link (akar -4)"
SEC_NGINX=$(docker exec "$CT_OO" sh -c \
    "grep -oP 'secure_link_secret \\K[A-Za-z0-9]+' /etc/nginx/conf.d/ds.conf 2>/dev/null | head -1" 2>/dev/null || echo "")
SEC_LOCAL=$(docker exec "$CT_OO" sh -c \
    "grep -oP 'secretString\"\\s*:\\s*\"\\K[^\"]+' /etc/onlyoffice/documentserver/local.json 2>/dev/null | head -1" 2>/dev/null || echo "")

if [ -z "$SEC_NGINX" ] || [ -z "$SEC_LOCAL" ]; then
    bad "kunci tidak terbaca (nginx='${#SEC_NGINX} kar' local='${#SEC_LOCAL} kar')"
    GAGAL=1
else
    S1=$(printf %s "$SEC_NGINX" | sha256sum | cut -c1-8)
    S2=$(printf %s "$SEC_LOCAL" | sha256sum | cut -c1-8)
    if [ "$S1" = "$S2" ]; then
        ok "kunci COCOK (sidik jari $S1, panjang ${#SEC_NGINX})"
    else
        bad "KUNCI BEDA → Editor.bin akan SELALU 403 → editor -4"
        info "ds.conf sha8=$S1  ·  local.json sha8=$S2"
        info "OBAT: bash scripts/perbaiki_oo.sh   (bagian 6b menyamakan + reload)"
        GAGAL=1
    fi
fi

# ── 2. Aset editor dari PUBLIK 200? ──────────────────────────────────
judul "2. Aset editor lewat domain"
KODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 \
    "$DOMAIN/oo/aset/web-apps/apps/api/documents/api.js" 2>/dev/null || echo 000)
if [ "$KODE" = "200" ]; then
    ok "api.js 200"
else
    bad "api.js = $KODE (harus 200) → editor tidak bisa dimuat"
    GAGAL=1
fi

# ── 3. Jejak NYATA: apakah Editor.bin 403? (bukti gejalanya) ─────────
judul "3. Jejak nyata Editor.bin / unduh / simpan (10 menit terakhir)"
N403=$(docker logs --since 10m "$CT_APP" 2>&1 | grep -c 'Editor.bin.*403' || true)
if [ "${N403:-0}" -gt 0 ]; then
    bad "$N403 permintaan Editor.bin ditolak 403 → dokumen TIDAK akan termuat"
    info "Ini gejala -4 'Unduhan gagal'. Obat: bash scripts/perbaiki_oo.sh"
    GAGAL=1
else
    ok "tidak ada Editor.bin yang ditolak (403) dalam 10 menit"
fi

N_UNDUH=$(docker logs --since 10m "$CT_APP" 2>&1 | grep -c 'oo/unduh.*200' || true)
N_BIN=$(docker logs --since 10m "$CT_APP" 2>&1 | grep -c 'Editor.bin.*200' || true)
N_SIMPAN=$(docker logs --since 10m "$CT_APP" 2>&1 | grep -c 'oo/simpan.*200' || true)
if [ "${N_UNDUH:-0}" -gt 0 ] && [ "${N_BIN:-0}" -gt 0 ]; then
    ok "alur editor TERBUKTI: unduh $N_UNDUH · Editor.bin $N_BIN · simpan $N_SIMPAN"
else
    warn "belum ada alur unduh+Editor.bin dalam 10 menit (editor belum dibuka siapa pun)"
    info "kalau mau bukti sekarang: buka /edit/<id> lalu ulangi gerbang ini"
fi

# ── KESIMPULAN ───────────────────────────────────────────────────────
echo
if [ "$GAGAL" -ne 0 ]; then
    echo "${MERAH}${TEBAL}⛔ GERBANG EDITOR GAGAL — editor BERISIKO -4.${NORMAL}"
    echo "   Obat tercepat: ${TEBAL}bash scripts/perbaiki_oo.sh${NORMAL}  lalu ulangi."
    exit 1
fi
echo "${HIJAU}${TEBAL}✅ GERBANG EDITOR LULUS — editor hidup.${NORMAL}"
echo
exit 0
