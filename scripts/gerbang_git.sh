#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
#  GERBANG GIT — menolak operasi yang bisa merusak branch produksi.
#
#  PEMAKAIAN:
#    bash scripts/gerbang_git.sh --periksa      Cek posisi sekarang (aman)
#    bash scripts/gerbang_git.sh --push         Push DENGAN pemeriksaan
#    bash scripts/gerbang_git.sh --pasang-hook  Pasang sebagai pre-push hook
#
#  ⚠️ BATAS JUJUR: skrip ini hanya berlaku KALAU DIJALANKAN.
#     Pagar UTAMA adalah izin tulis GitHub (agen luar = read-only).
#     Skrip ini pagar lapis kedua, bukan pengganti izin.
# ═══════════════════════════════════════════════════════════════════════
set -uo pipefail

MERAH=$'\033[31m'; HIJAU=$'\033[32m'; KUNING=$'\033[33m'; TEBAL=$'\033[1m'; MATI=$'\033[0m'
GAGAL=0
NAMA_REPO="eduai-publishing"
PEMILIK="PaculDigital"
BRANCH_PRODUKSI="main"

lulus() { echo "  ${HIJAU}✅${MATI} $1"; }
gagal() { echo "  ${MERAH}⛔${MATI} $1"; GAGAL=$((GAGAL + 1)); }
ingat() { echo "  ${KUNING}⚠️ ${MATI} $1"; }
judul() { echo; echo "${TEBAL}$1${MATI}"; }

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "${MERAH}Bukan repo git.${MATI}"; exit 2
}

BRANCH_KINI="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '(lepas)')"
ORIGIN_URL="$(git remote get-url origin 2>/dev/null || echo '')"

# ── Pemilik repo boleh push ke main & boleh origin = repo pemilik.
#    Agen luar TIDAK. Ditentukan dari git config lokal (diset sekali oleh Bos).
PEMILIK_LOKAL="$(git config --local --get eduai.pemilik 2>/dev/null || echo '')"
if [ "$PEMILIK_LOKAL" = "1" ]; then
  MODE="PEMILIK"
else
  MODE="AGEN"
fi

# ── Fungsi: apakah URL menunjuk ke repo PEMILIK (bukan fork sendiri)?
jalur_repo() {
  # keluarkan https://host/pemilik/repo(.git) → pemilik/repo
  echo "$1" | sed -E 's#^[a-z]+://[^/]+/##; s#\.git$##; s#/$##'
}

repo_origin="$(jalur_repo "$ORIGIN_URL")"

# ═══════════════════════════════════════════════════════════════════════
periksa() {
  echo "${TEBAL}════════════════════════════════════════════════════════${MATI}"
  echo "${TEBAL}  GERBANG GIT — ${NAMA_REPO}  [mode: ${MODE}]${MATI}"
  echo "${TEBAL}════════════════════════════════════════════════════════${MATI}"

  judul "1. Remote origin — harus FORK SENDIRI, bukan repo pemilik"
  if [ -z "$ORIGIN_URL" ]; then
    gagal "remote 'origin' belum ada"
  elif [ "$repo_origin" = "$PEMILIK/$NAMA_REPO" ]; then
    if [ "$MODE" = "PEMILIK" ]; then
      lulus "origin = repo pemilik (mode PEMILIK — sah)"
    else
      gagal "origin menunjuk ke repo PEMILIK ($repo_origin)"
      echo "        → Ini clone repo pemilik, bukan fork. JANGAN push dari sini."
      echo "        → Fork dulu, clone fork, lalu kerja di sana."
    fi
  else
    lulus "origin = $repo_origin (bukan repo pemilik)"
  fi

  judul "2. Branch sekarang — TIDAK BOLEH main (kecuali pemilik)"
  if [ "$BRANCH_KINI" = "$BRANCH_PRODUKSI" ]; then
    if [ "$MODE" = "PEMILIK" ]; then
      ingat "di branch '${BRANCH_PRODUKSI}' — sah untuk PEMILIK, tapi hati-hati"
    else
      gagal "sedang di branch '${BRANCH_PRODUKSI}' (PRODUKSI)"
      echo "        → Buat branch sendiri: git checkout -b agen/<nama>/<tujuan>"
    fi
  else
    lulus "branch = $BRANCH_KINI"
    # pola nama branch
    case "$BRANCH_KINI" in
      agen/*/*) lulus "nama branch berpola agen/<nama>/<tujuan>" ;;
      *) ingat "nama branch tidak berpola 'agen/<nama>/<tujuan>' (disarankan)" ;;
    esac
  fi

  judul "3. Remote 'hulu' — kalau ada, TIDAK BOLEH bisa di-push"
  if git remote | grep -qx hulu; then
    url_push="$(git remote get-url --push hulu 2>/dev/null || echo '')"
    if [ "$url_push" = "NO_PUSH_KE_HULU" ]; then
      lulus "hulu terkunci (tidak bisa di-push)"
    elif [ "$(jalur_repo "$url_push")" = "$PEMILIK/$NAMA_REPO" ]; then
      gagal "hulu MASIH BISA di-push ke repo pemilik"
      echo "        → Kunci sekarang: git remote set-url --push hulu NO_PUSH_KE_HULU"
    else
      lulus "hulu tidak menunjuk repo pemilik"
    fi
  else
    ingat "remote 'hulu' tidak ada (tidak wajib, tapi berguna untuk tarik update)"
  fi

  judul "4. Rahasia — tidak boleh ada yang ter-commit"
  bocor="$(git diff --cached --name-only 2>/dev/null \
    | grep -iE '(^|/)\.env($|\.)|secret|credential|\.pem$|\.key$|(^|/)data/.*\.(db|sqlite3?)$|token.*\.json$' \
    | grep -viE '\.env\.example$' || true)"
  if [ -n "$bocor" ]; then
    gagal "berkas rawan rahasia STAGED:"
    echo "$bocor" | sed 's/^/        ⛔ /'
    echo "        → Keluarkan: git restore --staged <berkas>"
  else
    lulus "tidak ada berkas rahasia ter-stage"
  fi

  judul "5. Berkas terlarang — tidak boleh diubah"
  DILARANG=".gitignore Dockerfile jalankan.sh ATURAN_BATAS_PROYEK_03OKT2026.md scripts/periksa_kode.sh"
  diubah=""
  for f in $DILARANG; do
    if ! git diff --quiet HEAD -- "$f" 2>/dev/null; then diubah="$diubah $f"; fi
  done
  if git diff --cached --name-only 2>/dev/null | grep -qE '^SOT_.*\.md$'; then
    diubah="$diubah SOT_*.md"
  fi
  if [ -n "$diubah" ]; then
    gagal "berkas yang TIDAK boleh diubah agen, tapi berubah:$diubah"
    echo "        → Ajukan usulan di deskripsi PR, jangan ubah sendiri."
  else
    lulus "berkas terlarang tidak tersentuh"
  fi

  judul "HASIL"
  if [ "$GAGAL" -eq 0 ]; then
    echo "  ${HIJAU}${TEBAL}✅ LULUS — aman untuk lanjut${MATI}"
    echo
    return 0
  fi
  echo "  ${MERAH}${TEBAL}⛔ GAGAL — ${GAGAL} masalah. JANGAN push.${MATI}"
  echo
  return 1
}

# ═══════════════════════════════════════════════════════════════════════
push_aman() {
  # dipanggil: --push [tujuan]
  TUJUAN="${1:-origin}"
  echo "${TEBAL}Pemeriksaan sebelum push…${MATI}"

  # 1. cek dasar
  if ! periksa; then
    echo "${MERAH}Push DIBATALKAN.${MATI}"
    return 1
  fi

  # 2. push ke main = HARAM untuk AGEN
  if [ "$BRANCH_KINI" = "$BRANCH_PRODUKSI" ] && [ "$MODE" != "PEMILIK" ]; then
    echo "${MERAH}⛔ Push ke '${BRANCH_PRODUKSI}' DIBATALKAN — branch produksi.${MATI}"
    return 1
  fi

  # 3. force push = HARAM (semua mode)
  for a in "$@"; do
    case "$a" in
      -f|--force|--force-with-lease*)
        echo "${MERAH}⛔ Force push DIBATALKAN.${MATI}"
        return 1 ;;
    esac
  done

  # 4. tujuan tidak boleh repo pemilik (kecuali mode PEMILIK)
  url_tujuan="$(git remote get-url --push "$TUJUAN" 2>/dev/null || echo '')"
  if [ "$(jalur_repo "$url_tujuan")" = "$PEMILIK/$NAMA_REPO" ] && [ "$MODE" != "PEMILIK" ]; then
    echo "${MERAH}⛔ Push ke repo PEMILIK DIBATALKAN (${PEMILIK}/${NAMA_REPO}).${MATI}"
    echo "   Ajukan Pull Request, jangan push langsung."
    return 1
  fi

  echo "${HIJAU}✅ Pemeriksaan lulus — push ke ${TUJUAN}/${BRANCH_KINI}${MATI}"
  git push -u "$TUJUAN" "$BRANCH_KINI"
}

# ═══════════════════════════════════════════════════════════════════════
pasang_hook() {
  HOOK=".git/hooks/pre-push"
  if [ -e "$HOOK" ] && ! grep -q "gerbang_git" "$HOOK" 2>/dev/null; then
    cp "$HOOK" "$HOOK.cadangan-$(date +%Y%m%d_%H%M%S)"
    echo "  hook lama dicadangkan"
  fi
  cat > "$HOOK" <<'HOOKEOF'
#!/usr/bin/env bash
# pre-push hook — dipasang oleh scripts/gerbang_git.sh
# Menolak push ke main dan force push.
remote="$1"; url="$2"
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '(lepas)')"
jalur="$(echo "$url" | sed -E 's#^[a-z]+://[^/]+/##; s#\.git$##; s#/$##')"

# Mode PEMILIK (diset: git config --local eduai.pemilik 1) dikecualikan
# dari dua cek pertama. Mode AGEN kena semua.
if [ "$(git config --local --get eduai.pemilik 2>/dev/null)" = "1" ]; then
  PEMILIK=1
else
  PEMILIK=0
fi

if [ "$PEMILIK" = "0" ] && [ "$jalur" = "PaculDigital/eduai-publishing" ]; then
  echo "⛔ pre-push: DILARANG push ke repo pemilik ($jalur)."
  echo "   Alur yang benar: fork → branch → Pull Request."
  exit 1
fi
if [ "$PEMILIK" = "0" ] && [ "$branch" = "main" ]; then
  echo "⛔ pre-push: DILARANG push dari branch 'main'."
  exit 1
fi

# tolak force push: kalau remote sudah punya commit yang tidak ada di lokal
while read -r lokal_sha lokal_ref jarak_sha remote_ref; do
  case "$lokal_ref" in refs/heads/*) ;; *) continue ;; esac
  if [ "$jarak_sha" != "0000000000000000000000000000000000000000" ]; then
    if ! git merge-base --is-ancestor "$jarak_sha" "$lokal_sha" 2>/dev/null; then
      echo "⛔ pre-push: FORCE PUSH terdeteksi (riwayat ditulis ulang). Dibatalkan."
      exit 1
    fi
  fi
done
exit 0
HOOKEOF
  chmod +x "$HOOK"
  echo "  ${HIJAU}✅ hook terpasang:${MATI} $HOOK"
  echo "  Mulai sekarang SETIAP 'git push' diperiksa otomatis."
}

# ═══════════════════════════════════════════════════════════════════════
case "${1:---periksa}" in
  --periksa)      periksa; exit $? ;;
  --push)         shift; push_aman "$@"; exit $? ;;
  --pasang-hook)  pasang_hook; exit 0 ;;
  -h|--help)
    echo "PEMAKAIAN: bash scripts/gerbang_git.sh [--periksa|--push|--pasang-hook]"
    echo
    echo "  --periksa       Cek posisi git sekarang (tidak mengubah apa pun)"
    echo "  --push [remote] Push dengan pemeriksaan (menolak main & force)"
    echo "  --pasang-hook   Pasang pre-push hook (pemeriksaan otomatis)"
    exit 0 ;;
  *) echo "Pilihan tidak dikenal: $1"; echo "Coba: bash scripts/gerbang_git.sh --help"; exit 2 ;;
esac
