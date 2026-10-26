#!/bin/bash
# Jalankan SEMUA gerbang EduAi dari DALAM container (cara BENAR) + periksa EXIT
cd /opt/data/services/eduai-publishing || exit 1
TOTAL_L=0; TOTAL_G=0; N_GERBANG=0; GAGAL_GERBANG=""
GERBANG="_gerbang_jurnal.py _gerbang_jurnal2.py _gerbang_jurnal3.py _gerbang_jatah.py
         _gerbang_rute_jurnal.py _gerbang_halaman_referensi.py _gerbang_kata_referensi.py
         _gerbang_ikon_referensi.py _gerbang_ikon_semua.py _gerbang_ikon_asli.py
         _gerbang_pagar_artikel.py _gerbang_unduh_workspace.py _gerbang_e2e_unduh_http.py
         _gerbang_unduh_dobel.py _gerbang_unduh_dobel_e2e.py
         _gerbang_link_jurnal.py
         _gerbang_skema_jev.py
         _gerbang_halaman_mutu.py
        _gerbang_indikator_artikel.py
        _gerbang_kutipan_scite.py
        _gerbang_kunci_layanan.py
        _gerbang_hemat_kuota.py
         _gerbang_sot.py
         app/_gerbang_format_standar.py
         app/_gerbang_pagar_unggah.py"
for g in $GERBANG; do
  #  GERBANG SOT butuh salinan dokumen + skrip gerbang + mesin sot.py.
  #  BERGIGI (26 Okt 2026, temuan agen Boss A): setiap cp SOT WAJIB dicek.
  #  Dulu semua cp ditelan >/dev/null 2>&1 tanpa cek gagal, dan daftarnya
  #  masih menyebut MASTER_PLAN/FLAG/CATATAN_PROYEK yang sudah diarsipkan.
  #  Daftar kini: SOT.md + docs/sot/* + sot.py + lampiran root (*.md).
  #  Gagal cp SOT = skrip BERHENTI di sini, bukan lanjut dengan hijau palsu.
  if [ "$g" = "_gerbang_sot.py" ]; then
    if ! docker cp sot.py eduai-app:/app/ >/dev/null 2>&1; then
      echo "  ❌ GAGAL cp sot.py ke container — gerbang SOT dibatalkan"; exit 1
    fi
    if ! docker exec eduai-app mkdir -p /app/sot-dok/docs/sot /app/sot-dok/_sketsa >/dev/null 2>&1; then
      echo "  ❌ GAGAL mkdir /app/sot-dok — gerbang SOT dibatalkan"; exit 1
    fi
    if ! docker cp SOT.md eduai-app:/app/sot-dok/ >/dev/null 2>&1; then
      echo "  ❌ GAGAL cp SOT.md — gerbang SOT dibatalkan"; exit 1
    fi
    if ! docker cp sot.py eduai-app:/app/sot-dok/sot.py >/dev/null 2>&1; then
      echo "  ❌ GAGAL cp sot.py ke sot-dok — gerbang SOT dibatalkan"; exit 1
    fi
    for d in docs/sot/*.md; do
      if ! docker cp "$d" eduai-app:/app/sot-dok/docs/sot/ >/dev/null 2>&1; then
        echo "  ❌ GAGAL cp $d — gerbang SOT dibatalkan"; exit 1
      fi
    done
    if ! docker cp _sketsa/jalankan_semua_gerbang.sh eduai-app:/app/sot-dok/_sketsa/ >/dev/null 2>&1; then
      echo "  ❌ GAGAL cp jalankan_semua_gerbang.sh — gerbang SOT dibatalkan"; exit 1
    fi
    #  Lampiran root (*.md) perlu IKUT supaya pemeriksa label jalan.
    for d in *.md; do
      if ! docker cp "$d" eduai-app:/app/sot-dok/ >/dev/null 2>&1; then
        echo "  ❌ GAGAL cp $d — gerbang SOT dibatalkan"; exit 1
      fi
    done
  fi
  docker cp "$g" eduai-app:/app/ >/dev/null 2>&1
  OUT=$(docker exec -w /app eduai-app python3 "$g" 2>&1); E=$?
  LINE=$(echo "$OUT" | grep -o 'TOTAL:.*' | tail -1)
  L=$(echo "$LINE" | grep -oP '\d+(?= LULUS)'); G=$(echo "$LINE" | grep -oP '\d+(?= GAGAL)')
  [ -z "$L" ] && L=0; [ -z "$G" ] && G=0
  TOTAL_L=$((TOTAL_L+L)); TOTAL_G=$((TOTAL_G+G)); N_GERBANG=$((N_GERBANG+1))
  [ "$E" != "0" ] && GAGAL_GERBANG="$GAGAL_GERBANG $g(EXIT=$E)"
  printf "  %-34s EXIT=%s  %s\n" "$g" "$E" "$LINE"
done
echo ""
echo "  ══ $N_GERBANG GERBANG: $TOTAL_L LULUS / $TOTAL_G GAGAL"
echo "  EXIT!=0:${GAGAL_GERBANG:- (tidak ada)}"
docker exec eduai-app sh -c 'rm -f /app/_gerbang_*.py /app/isi_artikel_uji.py /app/gerbang_naskah_isi.py; rm -rf /app/sot-dok' 2>/dev/null
echo "  (gerbang dibersihkan dari container)"
