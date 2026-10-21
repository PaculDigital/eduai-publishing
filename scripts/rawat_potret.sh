#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
#  rawat_potret.sh — RAWAT PROFIL CHROME UNTUK POTRET (STANDAR 25Sep26)
# ═══════════════════════════════════════════════════════════════════════════
#
#  PERINTAH BOS (25Sep26, verbatim):
#    "setiap mulai naik itu uji atau apapun sekali dengan profil yang baru
#     dan kosongkan profil uji lainnya yang sudah ada. Jadi tidak berat.
#     Ini standard nya"
#
#  ATURAN:
#   1. Chrome potret = SATU profil setiap kali uji naik (profil BARU).
#   2. Profil uji LAMA dihapus → tidak menumpuk → tidak berat.
#   3. SATU Chrome saja yang hidup (port 9333). Port 9341 dimatikan.
#
#  PAKAI:
#    bash scripts/rawat_potret.sh            # tampilkan keadaan
#    bash scripts/rawat_potret.sh --bersih   # hentikan Chrome mati + hapus profil lama
#    bash scripts/rawat_potret.sh --mulai    # profil BARU + Chrome hidup di 9333
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail

#  ⚠️ SATU VERSI SAJA (putusan Bos 11Okt26): "Hapus yg rusak, pakai satu versi saja."
#     Terukur 11Okt26: chromium-152 PRO = RUSAK (Trace/breakpoint trap, exit 133)
#     walau binary sehat — SEMUA mode (headless/headed/Xvfb) crash.
#     chromium-146 = TERBUKTI HIDUP (exit 124 = tetap jalan sampai timeout).
#     ⇒ 152 dihapus; 146 jadi SATU-SATUNYA. JANGAN pakai "versi terbaru" naif.
CARI_CHROME() {
  local p
  p=$(ls -d /opt/data/.cloakbrowser/chromium-*/chrome 2>/dev/null | sort -V | tail -1)
  [ -z "$p" ] && p=$(ls -d /opt/data/home/.cloakbrowser/chromium-*/chrome 2>/dev/null | sort -V | tail -1)
  [ -z "$p" ] && { echo "GAGAL: tidak ada binary chrome di ~/.cloakbrowser/" >&2; exit 1; }
  echo "$p"
}
CHROME="$(CARI_CHROME)"
PORT=9333
BARU="/tmp/chrome-uji-baru"

g() { printf '\033[1;36m%s\033[0m\n' "$1"; }
ok() { printf '   \033[1;32m✅ %s\033[0m\n' "$1"; }
warn() { printf '   \033[1;33m⚠️  %s\033[0m\n' "$1"; }

g "══ KEADAAN PROFIL CHROME ══"
echo "   binary: $CHROME"
[ -x "$CHROME" ] || { warn "BINARY CHROME TIDAK ADA/TAK BISA DIJALAN: $CHROME"; exit 1; }

#  ── 1. Chrome yang HIDUP ────────────────────────────────────────────────
g "[1] Chrome yang hidup"
HIDUP=""
for p in 9333 9341; do
  if curl -s -m 3 "http://127.0.0.1:$p/json/version" >/dev/null 2>&1; then
    VER=$(curl -s -m 3 "http://127.0.0.1:$p/json/version" | grep -o '"Browser":"[^"]*"' | cut -d'"' -f4)
    N=$(curl -s -m 3 "http://127.0.0.1:$p/json/list" | grep -c '"type"' || echo 0)
    ok "port $p hidup · $VER · $N tab"
    HIDUP="$HIDUP $p"
  else
    echo "   port $p mati"
  fi
done

#  ── 2. Pemakai disk ────────────────────────────────────────────────────
g "[2] Pemakai disk (yang bikin berat)"
for d in /tmp/chrome-* /tmp/org.chromium.Chromium.scoped_dir.*; do
  [ -e "$d" ] && du -sh "$d" 2>/dev/null
done | sort -rh | head -8
echo
echo "   TOTAL /tmp: $(du -sh /tmp 2>/dev/null | cut -f1)"
N_SCOPE=$(find /tmp -maxdepth 1 -name "org.chromium.Chromium.scoped_dir.*" 2>/dev/null | wc -l)
echo "   folder sampah org.chromium.scoped_dir.*: $N_SCOPE buah"

#  ── 3. Mode kerja ──────────────────────────────────────────────────────
if [ "${1:-}" = "--bersih" ] || [ "${1:-}" = "--mulai" ]; then
  g "[3] BERSIHKAN profil uji lama"

  #  3a. Hentikan Chrome 9341 (tak dipakai untuk potret) + semua anaknya
  if curl -s -m 3 http://127.0.0.1:9341/json/version >/dev/null 2>&1; then
    PID9341=$(pgrep -f "remote-debugging-port=9341" | head -1)
    if [ -n "$PID9341" ]; then
      kill "$PID9341" 2>/dev/null && ok "Chrome 9341 dihentikan (pid $PID9341)"
    fi
  else
    echo "   9341 sudah mati"
  fi

  #  3b. Hentikan Chrome 9333 lama — HANYA kalau diminta --mulai
  if [ "${1:-}" = "--mulai" ]; then
    if curl -s -m 3 http://127.0.0.1:9333/json/version >/dev/null 2>&1; then
      PID9333=$(pgrep -f "remote-debugging-port=9333" | head -1)
      [ -n "$PID9333" ] && kill "$PID9333" 2>/dev/null && ok "Chrome 9333 lama dihentikan (pid $PID9333)"
    fi
  fi

  #  3c. Buang profil uji lama + folder sampah (JANGAN sentuh profile eduai/kerja lain)
  for d in /tmp/chrome-9333 /tmp/chrome-tahap2 /tmp/chrome-tinjau /tmp/chrome-bayana \
           /tmp/chrome-uji-*; do
    [ -d "$d" ] && rm -rf "$d" && ok "dibuang: $d"
  done
  rm -rf /tmp/org.chromium.Chromium.scoped_dir.* 2>/dev/null
  rm -f /tmp/org.chromium.Chromium.?????? 2>/dev/null
  ok "folder sampah org.chromium.* dibersihkan"

  if [ "${1:-}" = "--mulai" ]; then
    g "[4] NYALAKAN profil BARU di :9333"
    rm -rf "$BARU"
    nohup "$CHROME" --headless=new --no-sandbox --disable-gpu \
      --remote-debugging-port=$PORT --remote-allow-origins='*' \
      --user-data-dir="$BARU" --window-size=1500,1400 about:blank \
      >/tmp/chrome-uji.log 2>&1 &
    for i in $(seq 1 30); do
      sleep 1
      if curl -s -m 3 "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
        ok "Chrome hidup di :$PORT (${i} dtk) · profil $BARU (BARU)"
        break
      fi
    done
  fi
fi

echo
echo "   TOTAL /tmp sesudah: $(du -sh /tmp 2>/dev/null | cut -f1)"
g "══ SELESAI ══"
