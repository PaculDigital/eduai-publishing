#!/usr/bin/env bash
#  GERBANG VISUAL EDUAI — periksa tampilan SUNGGUHAN lewat browser (CDP :9333)
#
#  Kenapa ada: Bos menemukan KOTAK PUTIH KOSONG di pojok header halaman Belajar
#  (04Okt26). Akar: kelas `kanan` dipakai 2 tempat (.atas .kanan = header,
#  .kanan{background:#fff} = kartu konten). DUA percobaan gerbang "baca CSS"
#  GAGAL (4 lalu 8 laporan PALSU) — pola `.a{}` + `.a b{}` itu SEHAT.
#  Putusan Bos = Opsi A: UKUR YANG DILIHAT MATA, bukan tebak kode.
#
#  Pakai: bash scripts/gerbang_visual.sh <url1> [url2 ...]
#  Balasan: 0 = bersih · 1 = ada temuan
set -uo pipefail

APP="$(cd "$(dirname "$0")/.." && pwd)"
if [ $# -eq 0 ]; then
  echo "Pakai: bash scripts/gerbang_visual.sh <url1> [url2 ...]"
  echo "Contoh: bash scripts/gerbang_visual.sh http://127.0.0.1:8002/belajar/insight/9?bab=1"
  exit 2
fi

#  CDP wajib hidup (kalau mati → browser gagal, BUKAN temuan tampilan)
KODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:9333/json/version || true)
if [ "$KODE" != "200" ]; then
  echo "⛔ CDP :9333 TIDAK HIDUP (balas $KODE) — browser gagal."
  echo "   Nyalakan dulu, lalu ulangi. Ini BUKAN temuan tampilan."
  exit 1
fi

cd "$APP"
python3 app/_gerbang_visual.py "$@"
