#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  ⚠️  BERKAS INI SUDAH DIPENSIUNKAN (30 Sep 2026)                         ║
# ║                                                                          ║
# ║  Ia dulu salinan "docker run" saja (tanpa build) — BERBAHAYA karena:     ║
# ║    • tag image di dalamnya BASI (pernah menunjuk image yang sudah        ║
# ║      dihapus → `docker rm -f` produksi dulu, baru GAGAL = PRODUKSI DOWN) ║
# ║    • tidak membangun image → kode di disk TIDAK ikut jalan               ║
# ║                                                                          ║
# ║  SEJAK 30Sep26 SKRIP RESMI = `jalankan.sh` di ROOT PROYEK:               ║
# ║      cd /opt/data/services/eduai-publishing && bash jalankan.sh          ║
# ║  Isinya 5 langkah: periksa kode → backup image+DB → build → VERIFIKASI   ║
# ║  ISI IMAGE → ganti container → gerbang jaringan/OnlyOffice/editor.       ║
# ║  (Pagar jaringan eduai-net + gerbang /oo/aset sudah PINDAH ke sana.)    ║
# ║                                                                          ║
# ║  Berkas ini sengaja TIDAK dihapus supaya rujukan lama di dokumentasi     ║
# ║  tidak menyesatkan — ia hanya MENGALIHKAN ke skrip resmi.                ║
# ╚══════════════════════════════════════════════════════════════════════════╝
set -uo pipefail

AKAR="$(cd "$(dirname "$0")/.." && pwd)"

cat <<'PESAN'
═══════════════════════════════════════════════════════════════════
  ⚠️  scripts/jalankan.sh SUDAH DIPENSIUNKAN — tidak dijalankan.
═══════════════════════════════════════════════════════════════════
  Skrip resmi sekarang: jalankan.sh di ROOT proyek (build IMAGE baru).

  Pakai:
      cd /opt/data/services/eduai-publishing
      bash jalankan.sh

  Kenapa dipensiunkan: salinan lama ini hanya `docker run` tanpa build,
  tag image-nya basi, dan pernah membuat produksi DOWN (rm container dulu,
  baru gagal). Semua pagar (jaringan eduai-net, /oo/aset, gerbang editor)
  sudah pindah ke skrip root.
═══════════════════════════════════════════════════════════════════
PESAN

if [ "${1:-}" = "--lanjut" ]; then
    echo "  → --lanjut diberikan: memanggil skrip RESMI di root..."
    exec bash "$AKAR/jalankan.sh" "${@:2}"
fi

echo
echo "  (Tambahkan --lanjut kalau memang mau menjalankan skrip resmi.)"
exit 0
