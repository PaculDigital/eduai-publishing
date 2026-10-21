#!/bin/bash
# BERSIH-BERSIH IMAGE DOCKER eduai-app — Opsi A (putusan Bos 07 Okt 2026).
#
# ATURAN KERAS:
#   · JANGAN hapus image YANG SEDANG JALAN (docker inspect eduai-app).
#   · JANGAN hapus TAG CADANGAN/titik mundur (cadangan-pra-*).
#   · HANYA hapus tag bertanggal `eduai-app:YYYYMMDD_HHMMSS-sot` yang LAMA.
#   · Simpan N terbaru (biar bisa mundur cepat).
#
# Pemakaian: bash skrip_ini.sh [jumlah_disimpan]   (default: 3)
set -u
SIMPAN="${1:-3}"
cd /opt/data/services/eduai-publishing || exit 1

JALAN="$(docker inspect eduai-app --format '{{.Config.Image}}' 2>/dev/null)"
[ -z "$JALAN" ] && { echo "  ❌ TIDAK BISA baca image yang jalan — BATAL"; exit 1; }
echo "  Image yang JALAN : $JALAN"

D="$(ls -dt _arsip/pre-bersih-A-* 2>/dev/null | head -1)"
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.CreatedAt}}' \
  | grep '^eduai-app' > "$D/daftar_image_SEBELUM.txt" 2>/dev/null
echo "  Daftar SEBELUM → $D/daftar_image_SEBELUM.txt"

#  Kumpulkan tag bertanggal (pola YYYYMMDD_HHMMSS-sot), urut BARU→LAMA.
mapfile -t TANGGAL < <(docker images --format '{{.Repository}}:{{.Tag}}' \
  | grep -E '^eduai-app:[0-9]{8}_[0-9]{6}-sot$' \
  | sort -r)

echo "  Tag bertanggal   : ${#TANGGAL[@]}"
echo "  Disimpan (N baru): $SIMPAN"
echo ""

hapus=()
for i in "${!TANGGAL[@]}"; do
  t="${TANGGAL[$i]}"
  #  (1) JANGAN sentuh yang sedang jalan
  if [ "$t" = "$JALAN" ]; then
    echo "  🛡️  SIMPAN (sedang jalan) : $t"
    continue
  fi
  #  (2) JANGAN sentuh tag cadangan / titik mundur
  case "$t" in
    *cadangan*|*mundur*|*rollback*) echo "  🛡️  SIMPAN (cadangan)     : $t"; continue;;
  esac
  #  (3) Simpan N terbaru
  if [ "$i" -lt "$SIMPAN" ]; then
    echo "  💾 SIMPAN (baru ke-$((i+1)))   : $t"
    continue
  fi
  hapus+=("$t")
done

echo ""
echo "  ══ CALON HAPUS: ${#hapus[@]} image ══"
for t in "${hapus[@]}"; do echo "     🗑️  $t"; done
echo ""

if [ "${#hapus[@]}" -eq 0 ]; then
  echo "  (tidak ada yang perlu dihapus)"; exit 0
fi

for t in "${hapus[@]}"; do
  #  Image yang masih dipakai container lain TIDAK akan terhapus oleh docker
  #  (aman: docker menolak). Jadi tidak perlu cek manual.
  out="$(docker rmi "$t" 2>&1)"
  if [ $? -eq 0 ]; then
    echo "  ✅ dihapus: $t"
  else
    echo "  ⏭️  dilewati (dipakai): $t"
  fi
done

echo ""
echo "  ══ SESUDAH ══"
echo "  total image eduai-app: $(docker images --format '{{.Repository}}' | grep -c '^eduai-app$')"
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.CreatedAt}}' \
  | grep '^eduai-app' > "$D/daftar_image_SESUDAH.txt" 2>/dev/null
echo "  Daftar SESUDAH → $D/daftar_image_SESUDAH.txt"
echo ""
echo "  ══ VERIFIKASI WAJIB ══"
echo "  image yang jalan masih ada? $(docker images --format '{{.Repository}}:{{.Tag}}' | grep -c "^${JALAN}$") (harus 1)"
echo "  container masih hidup?      $(docker inspect eduai-app --format '{{.State.Status}}' 2>/dev/null)"
echo "  /health                     $(curl -s -o /dev/null -w '%{http_code}' https://eduai.bikinaja.id/health 2>/dev/null)"
