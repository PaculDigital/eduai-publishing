#!/bin/bash
# Uji statis perbaikan gerbang BUKU LATAR (30 Okt 2026). Hanya isi berkas, tanpa docker.
cd "$(dirname "$0")" || exit 1
LULUS=0; GAGAL=0
cek() {
  local nama="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "  OK $nama"; LULUS=$((LULUS+1)); else echo "  GAGAL $nama"; GAGAL=$((GAGAL+1)); fi
}
cek "sintaks periksa" bash -n scripts/periksa_kode.sh
cek "sintaks jalankan" bash -n jalankan.sh
cek "tanpa fallback docker images" bash -c '! grep -q "docker images --format" scripts/periksa_kode.sh'
cek "pesan image eksplisit ada" grep -q "butuh image eksplisit" scripts/periksa_kode.sh
cek "skip pra-build ada" grep -q "PERIKSA_TANPA_BUKU_LATAR" scripts/periksa_kode.sh
cek "langkah 0 pakai skip" grep -q "PERIKSA_TANPA_BUKU_LATAR=1 bash scripts/periksa_kode.sh" jalankan.sh
cek "langkah 4 pakai image baru" grep -q 'bash scripts/periksa_kode.sh --image "${IMAGE_BASE}:${TAG}"' jalankan.sh
N_BUILD=$(grep -n 'docker build -t' jalankan.sh | head -1 | cut -d: -f1)
N_GERBANG=$(grep -n 'bash scripts/periksa_kode.sh --image' jalankan.sh | head -1 | cut -d: -f1)
N_RUN=$(grep -n '5/5' jalankan.sh | head -1 | cut -d: -f1)
if [ -n "$N_BUILD" ] && [ -n "$N_GERBANG" ] && [ -n "$N_RUN" ] && [ "$N_BUILD" -lt "$N_GERBANG" ] && [ "$N_GERBANG" -lt "$N_RUN" ]; then
  echo "  OK urutan build < gerbang < langkah 5 ($N_BUILD < $N_GERBANG < $N_RUN)"; LULUS=$((LULUS+1))
else
  echo "  GAGAL urutan build < gerbang < langkah 5 ($N_BUILD < $N_GERBANG < $N_RUN)"; GAGAL=$((GAGAL+1))
fi
echo "UJI GERBANG: $LULUS lolos, $GAGAL gagal"
[ "$GAGAL" -eq 0 ]
