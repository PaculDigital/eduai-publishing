#!/bin/bash
# TAR backup berkas berharga sebelum bersih (eduai-publishing, 26Sep26)
set -e
cd /opt/data/services/eduai-publishing
TS=26Sep1638
DEST=_arsip/pre-bersih-keseluruhan-$TS
mkdir -p "$DEST"

# daftar eksplisit, error kalau ada pola tanpa match (nullglob)
shopt -s nullglob
berkas=(
  shots/
  docs/ilustrasi_fe
  _uji_web/
  AI_hubungan.png AI_komposisi.png AI_sebaran.png AI_tahunan.png
  FINAL_batang.png FINAL_garis.png FINAL_histogram.png FINAL_pai.png FINAL_sebar.png
  GAYA2_01_korporat_biru.png GAYA2_02_modern.png GAYA2_03_majalah_ilmiah.png
  GAYA3_modern_tebal.png GAYA4_modern_final.png
  SKETSA_01_korporat_biru.png SKETSA_02_modern.png SKETSA_03_majalah_ilmiah.png
  V5_*.png UJI_judul_panjang.png
  MESIN_batang.png MESIN_garis.png MESIN_histogram.png MESIN_pai.png
  HASIL_C_grafik_ai.png HASIL_C_naskah_dengan_grafik.docx
)
tar czf "$DEST/kembalikan-jika-perlu.tar.gz" "${berkas[@]}"
ls -lh "$DEST/kembalikan-jika-perlu.tar.gz"
echo "OK"
