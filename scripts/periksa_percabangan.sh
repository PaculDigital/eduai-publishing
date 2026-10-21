#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════
#  PERIKSA PERCABANGAN EDUAI — penangkap cabang yang MENGGANTUNG.
#
#  KENAPA ADA (perintah Bos 24Sep26: "Update dulu Dokumentasi, skill,
#  script dan catatan. Agar tetap menjadi SOT, tentang percabangan ini
#  juga di catat.").
#
#  MASALAH YANG DITUTUP: SOT (FLAG/MASTER_PLAN) bisa BASI diam-diam.
#  Contoh nyata: MASTER_PLAN §7 masih "13 Sep 2026" padahal sudah 24 Sep
#  dan banyak barisnya sudah SALAH ("kuota AI belum dibangun" — padahal
#  SUDAH JALAN). Tidak ada penangkap → 11 hari basi tanpa ketahuan.
#
#  PAKAI:  bash scripts/periksa_percabangan.sh
#  Keluar 0 = SOT SELARAS (tanggal segar + semua cabang tercatat).
#  Keluar 1 = ADA YANG BASI / TIDAK TERCATAT.
#
#  ⚠️ INI PENANGKAP, BUKAN PENGHUKUM: setiap temuan disertai CARA BETULKAN.
# ══════════════════════════════════════════════════════════════════════════
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"
PETA="PETA_PERCABANGAN_24SEP2026.md"
LULUS=0
GAGAL=0

hijau() { printf '  ✅ %s\n' "$*"; LULUS=$((LULUS + 1)); }
merah() {
  printf '  ❌ %s\n' "$*"
  GAGAL=$((GAGAL + 1))
}

echo
echo "═══════════════════════════════════════════════════════════════"
echo "  PERIKSA PERCABANGAN EDUAI — apakah SOT masih sah?"
echo "═══════════════════════════════════════════════════════════════"

# ── 1. Berkas peta percabangan harus ADA ──────────────────────────────
echo
echo "── [1] Berkas peta percabangan ──"
if [ -f "$PETA" ]; then
  hijau "$PETA ada ($(wc -c <"$PETA") byte)"
else
  merah "$PETA HILANG — peta cabang tidak ada, SOT tidak punya acuan."
  echo "      → BETULKAN: buat berkas itu (lihat riwayat git / FLAG_LANJUT_DISINI.md)"
fi

# ── 2. Tanggal SOT harus SEGAR (≤ 7 hari) ─────────────────────────────
echo
echo "── [2] Kesegaran tanggal SOT ──"
# Tanggal terbaru yang disebut di dua berkas SOT (format: DD Mon YYYY
# atau D Mon YYYY, mis. "24 Sep 2026").
_terbaru() {
  grep -oE '[0-9]{1,2} (Jan|Feb|Mar|Apr|Mei|May|Jun|Jul|Agu|Aug|Sep|Okt|Oct|Nov|Des|Dec) 20[0-9]{2}' "$1" 2>/dev/null \
    | sort -u | while read -r t; do
      d=$(echo "$t" | cut -d' ' -f1)
      m=$(echo "$t" | cut -d' ' -f2)
      y=$(echo "$t" | cut -d' ' -f3)
      case "$m" in
        Jan) mm=01 ;; Feb) mm=02 ;; Mar) mm=03 ;; Apr) mm=04 ;;
        Mei|May) mm=05 ;; Jun) mm=06 ;; Jul) mm=07 ;;
        Agu|Aug) mm=08 ;; Sep) mm=09 ;; Okt|Oct) mm=10 ;;
        Nov) mm=11 ;; Des|Dec) mm=12 ;;
      esac
      printf '%s-%s-%02d\n' "$y" "$mm" "$d"
    done | sort | tail -1
}
for f in "$PETA" MASTER_PLAN.md FLAG_LANJUT_DISINI.md; do
  [ -f "$f" ] || continue
  tgl=$(_terbaru "$f")
  if [ -z "$tgl" ]; then
    merah "$f — tidak ada tanggal terbaca."
    continue
  fi
  umur=$(( ($(date +%s) - $(date -d "$tgl" +%s)) / 86400 ))
  if [ "$umur" -le 7 ]; then
    hijau "$f — tanggal terbaru $tgl (umur ${umur} hari)"
  else
    merah "$f — tanggal terbaru $tgl = BASI ${umur} hari."
    echo "      → BETULKAN: perbarui bagian status + tanggal 'Terakhir diperbarui'"
  fi
done

# ── 3. Setiap cabang C1..C7 harus TERCATAT di peta ────────────────────
echo
echo "── [3] Kelengkapan cabang C1–C9 ──"
for c in C1 C2 C3 C4 C5 C6 C7 C8 C9; do
  if grep -qF "$c" "$PETA" 2>/dev/null; then
    hijau "cabang $c tercatat"
  else
    merah "cabang $c TIDAK tercatat di $PETA"
    echo "      → BETULKAN: tambahkan baris cabang $c (keadaan + yang kurang)"
  fi
done

# ── 4. Bukti HARUS bisa diperiksa: kode lama tidak boleh jadi 'selesai' ─
echo
echo "── [4] Cabang yang diklaim 'TERBUKTI MASIH ADA' harus benar ada ──"
if docker ps --filter name=eduai-app --format '{{.Names}}' 2>/dev/null | grep -q eduai-app; then
  # C4 DITUTUP 24Sep26 → penangkap SEKARANG menuntut kebalikannya:
  # `_deteksi_bagian` WAJIB ada di endpoint /bab. Kalau hilang = C4 kembali.
  if docker exec eduai-app grep -q 'dari_bagian = _deteksi_bagian' /app/app/ai.py 2>/dev/null; then
    hijau "C4 tetap TERTUTUP: endpoint /bab pakai _deteksi_bagian (sub-bab)"
  else
    merah "C4 KEMBALI! endpoint /bab tidak memakai _deteksi_bagian lagi."
    echo "      → BETULKAN: 'daftar = dari_bagian if dari_bagian else deteksi_bab(teks)' di app/ai.py"
  fi
  # T3.3 & Fase 6 harus tetap BELUM ada; kalau sudah ada, peta basi.
  for pola in 'kunci_naskah' 'def sitasi'; do
    if docker exec eduai-app grep -rq "$pola" /app/app/ 2>/dev/null; then
      merah "'$pola' sudah ADA di produksi tapi peta bilang BELUM dibangun."
      echo "      → BETULKAN: perbarui daftar 'BELUM DIBANGUN'"
    else
      hijau "'$pola' benar masih belum ada (sesuai peta)"
    fi
  done
else
  merah "container eduai-app tidak jalan — tidak bisa periksa isi."
  echo "      → JALANKAN: docker ps --filter name=eduai-app"
fi

# ── 5. KESIAPAN DATA UJI + PAGAR C9 (25Sep26) ─────────────────────────
#  KENAPA: 24Sep26 gerbang gagal 5 grup HANYA karena data uji dibersihkan
#  (user uji + VersiDokumen sumber 'uji' + profil_dokumen). Itu GAGAL PALSU,
#  bukan bug app. Penangkap ini memperingatkan SEBELUM gerbang jalan.
#
#  🔄 25Sep26: `_uji_fase5_jalur` SUDAH DIPERBAIKI (C8) — ia tidak lagi
#  bergantung pada `profil_dokumen`, melainkan memakai DOKUMEN UJI di
#  `_contoh-dokumen/` + `petakan()` langsung. Jadi temuan `profil_dokumen=0`
#  TIDAK LAGI menggagalkan uji → cukup jadi CATATAN (bukan merah).
#
#  Sebagai gantinya, §5 sekarang juga MENUNTUT pagar C9 masih ada —
#  supaya perbaikan "sukses palsu" tidak bisa dicabut diam-diam.
echo
echo "── [5] Kesiapan data uji + pagar C9 ──"
if docker ps --filter name=eduai-app --format '{{.Names}}' 2>/dev/null | grep -q eduai-app; then
  hasil=$(docker exec eduai-app python3 -c "
import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
def n(q):
    try: return c.execute(q).fetchone()[0]
    except Exception: return -1
print(n(\"select count(*) from users where email like '%uji%'\"))
print(n('select count(*) from versi_dokumen'))
print(n('select count(*) from profil_dokumen'))
print(n('select count(*) from files'))
print(n('select count(*) from versi_dokumen where length(isi)=0 and terpakai=1'))
" 2>/dev/null)
  uji=$(echo "$hasil" | sed -n 1p)
  versi=$(echo "$hasil" | sed -n 2p)
  profil=$(echo "$hasil" | sed -n 3p)
  files=$(echo "$hasil" | sed -n 4p)
  kosong=$(echo "$hasil" | sed -n 5p)
  echo "     user uji=$uji · versi_dokumen=$versi · profil_dokumen=$profil · files=$files"
  if [ "${uji:-0}" -ge 1 ] 2>/dev/null; then
    hijau "user uji ada ($uji)"
  else
    merah "user uji TIDAK ADA → uji pembimbing akan gagal PALSU."
    echo "      → BETULKAN: jalankan _sketsa/siapkan_uji_25.py (data uji saja)"
  fi
  #  C8 sudah diperbaiki → profil_dokumen=0 cuma CATATAN, bukan lagi penghalang.
  if [ "${profil:-0}" -ge 1 ] 2>/dev/null; then
    hijau "profil_dokumen terisi ($profil)"
  else
    printf '  ℹ️  profil_dokumen kosong (%s) — C8 sudah diperbaiki, uji fase5\n' "$profil"
    echo "        memakai _contoh-dokumen/ jadi TIDAK gagal. (dulu: gagal palsu)"
  fi
  #  🚨 PAGAR C9: TIDAK BOLEH ada versi KOSONG yang sedang DIPAKAI.
  if [ "${kosong:-0}" -eq 0 ] 2>/dev/null; then
    hijau "pagari C9: tidak ada versi KOSONG yang terpakai"
  else
    merah "ADA $kosong versi 0-karakter berstatus terpakai → naskah bisa KOSONG (C9)."
    echo "      → PERIKSA: versi_dokumen where length(isi)=0 and terpakai=1"
    echo "      → PULIHKAN dengan mengembalikan ke versi sebelumnya (perlu ACC Bos)"
  fi
else
  merah "container eduai-app tidak jalan — kesiapan data uji tidak bisa diperiksa."
  echo "      → JALANKAN: docker ps --filter name=eduai-app"
fi

# ── 6. Rangkuman ──────────────────────────────────────────────────────
echo
echo "═══════════════════════════════════════════════════════════════"
if [ "$GAGAL" -eq 0 ]; then
  printf '  ✅ SOT PERCABANGAN SELARAS — %d lulus / 0 gagal\n' "$LULUS"
  echo "═══════════════════════════════════════════════════════════════"
  exit 0
fi
printf '  ❌ ADA %d TEMUAN / %d lulus — SOT PERLU DIPERBARUI\n' "$GAGAL" "$LULUS"
echo "     (setiap temuan sudah disertai CARA BETULKAN di atas)"
echo "═══════════════════════════════════════════════════════════════"
exit 1
