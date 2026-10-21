#!/usr/bin/env bash
#  ═══════════════════════════════════════════════════════════════════════════
#  salin_restart.sh — STANDAR WAJIB MENYALIN KODE KE KONTAINER (ACC Bos 24Sep26)
#  ═══════════════════════════════════════════════════════════════════════════
#
#  🚨 KENAPA SKRIP INI ADA (akar, terukur 24Sep26):
#
#  `docker cp` HANYA menukar berkas di disk container. Server yang SEDANG
#  JALAN tidak membaca ulang berkas itu — karena `eduai-app` dijalankan
#  `uvicorn app.main:app` TANPA `--reload`: kode dimuat SEKALI saat start.
#
#  AKIBAT NYATA: container hidup 8 jam, Wulan `docker cp` berkali-kali, dan
#  baris pengintai `log.warning('[INTIP] ...')` muncul 0 KALI. Artinya
#  SELURUH perubahan — termasuk yang sudah dilaporkan "teruji" — sebenarnya
#  memakai KODE LAMA. Wulan menguji barang yang salah, lalu salah lapor.
#
#  ⇒ SATU-SATUNYA cara pasti: sesudah menyalin, KONTAINER HARUS DIMULAI
#    ULANG (`docker restart`), baru verifikasi `/health`.
#
#  ⚠️ CATATAN PENTING agar tidak salah paham:
#    - Ini untuk UJI CEPAT (menyalin 1-2 berkas sambil mencari akar bug).
#    - Untuk TAYANG PRODUKSI tetap `bash jalankan.sh` (build IMAGE baru).
#      Deploy memang tidak kena masalah ini — image-nya baru.
#    - `docker restart` TIDAK membaca ulang `.env` (env ditempel saat
#      `docker run`) → kalau yang diubah `.env`, WAJIB `jalankan.sh`.
#
#  ⚠️ JEBAKAN yang sudah dibayar mahal: sync `sh` → 2 JAM TIDAK NYALA.
#    Container hidup lagi, tapi aplikasi TIDAK melayani port → curl hang
#    selamanya, dan Wulan menyimpulkan "aplikasi rusak". Karena itu skrip
#    ini WAJIB memeriksa `docker inspect .State.Health.Status` dulu
#    (TIDAK bergantung `curl` yang bisa menggantung).
#
#  ═══ CARA PAKAI ═══════════════════════════════════════════════════════════
#    bash scripts/salin_restart.sh eduai-app app/sorotan.py app/rute_pembimbing.py
#        → banyak berkas sekaligus: restart HANYA SEKALI (hemat 10 detik/berkas)
#
#    bash scripts/salin_restart.sh eduai-app --periksa
#        → hanya periksa: apakah container benar-benar sudah memakai kode baru
#  ═══════════════════════════════════════════════════════════════════════════
set -u

APP="${1:-}"; shift || true
[ -z "$APP" ] && { echo "  ❌ sebut nama container. Contoh: bash scripts/salin_restart.sh eduai-app app/sorotan.py"; exit 2; }

DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR" || exit 1

HIJAU=$'\033[32m'; MERAH=$'\033[31m'; KUNING=$'\033[33m'; MATI=$'\033[0m'

#  ── Tunggu sampai aplikasi BENAR-BENAR melayani ───────────────────────────
#  ⚠️ AKAR BUG SKRIP 24Sep26 (ketemu dari uji skripnya sendiri):
#  Versi pertama MENUNGGU `docker inspect .State.Health.Status == healthy`.
#  Kenyataannya container `eduai-app` TIDAK PUNYA healthcheck →
#  statusnya `none` → penunggu berputar 40×10 dtk sia-sia lalu MELAPORKAN
#  "BELUM melayani", padahal `/health` = **200** (aplikasi SEHAT, terukur).
#  Itu pelajaran lama Wulan sendiri: SYARAT yang tidak dibutuhkan → GAGAL
#  PALSU. ⇒ Sekarang `/health` (dari DALAM container) jadi UKURAN UTAMA —
#  itu bukti aplikasi benar-benar menjawab, bukan sekadar wadah hidup.
#  Healthcheck hanya dipakai sebagai "tunggu dulu" kalau MEMANG ada.
tunggu_sehat() {
  printf '  ⏳ menunggu aplikasi menjawab…'
  for _ in $(seq 1 45); do
    kode=$(docker exec "$APP" curl -s -m 3 -o /dev/null \
             -w '%{http_code}' http://127.0.0.1:8000/health 2>/dev/null)
    if [ "$kode" = "200" ]; then
      printf ' siap.\n'
      return 0
    fi
    #  Wadah masih "restarting"/"exited" → pasti belum bisa menjawab.
    jalan=$(docker inspect "$APP" --format '{{.State.Status}}' 2>/dev/null)
    if [ "$jalan" = "exited" ] || [ "$jalan" = "dead" ]; then
      printf ' wadah %s.\n' "$jalan"
      return 1
    fi
    printf '.'
    sleep 1
  done
  printf ' belum (kode terakhir: %s).\n' "${kode:-tidak ada}"
  return 1
}

#  ── Mode --periksa: buktikan kode baru benar-benar dipakai ────────────────
if [ "${1:-}" = "--periksa" ]; then
  echo "════ PERIKSA KONTAINER $APP ════"
  echo "  mulai terakhir : $(docker inspect "$APP" --format '{{.State.StartedAt}}' 2>/dev/null)"
  echo "  sekarang (UTC) : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "  perintah       : $(docker inspect "$APP" --format '{{json .Config.Cmd}}' 2>/dev/null)"
  echo "  kesehatan      : $(docker inspect "$APP" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null)"
  echo "  /health        : $(docker exec "$APP" curl -s -m 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/health 2>/dev/null)"
  echo
  echo "  ⚠️ Kalau perintahnya TIDAK memuat '--reload', maka setiap"
  echo "     docker cp WAJIB lewat skrip ini (harus restart)."
  exit 0
fi

#  ── Salin berkas ──────────────────────────────────────────────────────────
if [ "$#" -eq 0 ]; then
  echo "  ❌ tidak ada berkas yang disebut. Contoh: bash scripts/salin_restart.sh $APP app/sorotan.py"
  exit 2
fi

GAGAL_SALIN=0
echo "════ SALIN + RESTART (standar wajib 24Sep26) ════"
for f in "$@"; do
  if [ ! -f "$DIR/$f" ]; then
    printf '  %s❌ %s%s  (berkas tidak ada di sumber)\n' "$MERAH" "$f" "$MATI"
    GAGAL_SALIN=1
    continue
  fi
  if docker cp "$DIR/$f" "$APP:/app/$f" >/dev/null 2>&1; then
    #  Buktikan ISI-nya benar-benar sama (bukan sekadar tidak error).
    host=$(md5sum "$DIR/$f" | cut -d' ' -f1)
    con=$(docker exec "$APP" md5sum "/app/$f" 2>/dev/null | cut -d' ' -f1)
    if [ "$host" = "$con" ]; then
      printf '  %s✅ %s%s  (md5 sama)\n' "$HIJAU" "$f" "$MATI"
    else
      printf '  %s❌ %s%s  (isi BERBEDA: host %s vs container %s)\n' "$MERAH" "$f" "$MATI" "${host:0:10}" "${con:0:10}"
      GAGAL_SALIN=1
    fi
  else
    printf '  %s❌ %s%s  (docker cp gagal)\n' "$MERAH" "$f" "$MATI"
    GAGAL_SALIN=1
  fi
done
[ "$GAGAL_SALIN" -ne 0 ] && { echo "  ❌ ada yang gagal disalin → JANGAN diuji dulu."; exit 1; }

#  ── RESTART: satu-satunya cara kode baru benar-benar dipakai ─────────────
echo "  🔄 restart $APP (kode dimuat ulang)…"
docker restart "$APP" >/dev/null 2>&1 || { echo "  ❌ restart gagal"; exit 1; }

if tunggu_sehat; then
  printf '  %s✅ %s sehat, /health 200 — kode BARU sudah dipakai%s\n' "$HIJAU" "$APP" "$MATI"
  echo "  ℹ️  Bukti lebih kuat (opsional): titipkan sebaris"
  echo "      log.warning('[INTIP] ...') di fungsi yang diuji, lalu:"
  echo "      docker logs --since 60s $APP | grep INTIP"
  exit 0
else
  printf '  %s❌ %s BELUM melayani — lihat: docker logs --tail 40 %s%s\n' \
    "$MERAH" "$APP" "$APP" "$MATI"
  exit 1
fi
