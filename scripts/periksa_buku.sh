#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
#  GERBANG BUKU — gerbang deploy untuk mesin buku
# ═══════════════════════════════════════════════════════════════════════
#
#  KEPUTUSAN BOS 27 Okt 2026 (Opsi C+A dari usulan sambung-gerbang):
#  mesin buku dijaga pada SETIAP deploy, sebelum jalankan.sh berjalan.
#
#  KENAPA BUKAN DI DALAM jalankan.sh:
#  jalankan.sh DILARANG diubah (AGEN_LUAR_ATURAN.md §4 — jalur deploy
#  resmi + urutan gerbang). Maka gerbang ini dipanggil dari PERINTAH
#  DEPLOY, sebelum jalankan.sh, dengan rantai && (gagal = deploy batal):
#
#    bash scripts/periksa_buku.sh && bash jalankan.sh
#
#  CARA PAKAI (dari root repo):
#    bash scripts/periksa_buku.sh
#
#  KELUAR 0 bila semua suite lulus. KELUAR 1 bila ada suite gagal ATAU
#  dilewati: SKIP di sini = GAGAL. Gerbang yang tidak menguji (perender
#  atau pdftotext tidak ada) = tidak menjaga, jadi harus menghentikan
#  deploy, bukan lolos diam-diam.
#
#  SUITE YANG DIJALANKAN (semua sudah ada di main, tanpa ubah apa pun):
#    1. JENIS ......... uji_gerbang_jenis.py  (spec -> gerbang jenis)
#    2. CHAPTER ....... uji_bergigi_v6.py     (bangun + gerbang chapter)
#    3. CARI-TOC ...... uji_cari_toc.py       (peta halaman TOC, WordCraft)
#    4. ISI-NOMOR-TOC . uji_isi_nomor_toc.py  (nomor TOC buku assembly)
#    5. REGRESI-EMAS .. uji_regresi_emas.py   (sidik jari vs emas; TANPA
#                                               --perbarui: gerbang ini
#                                               tidak pernah menulis emas)
#
#  PRASYARAT (diperiksa dulu, gagal = berhenti):
#    python3 + python-docx, wordcraft-cli, pdftotext.
#    WordCraft dicari: $WORDCRAFT_CLI -> PATH -> salinan hermes
#    (/opt/data/services/wordcraft-uji/bin/wordcraft-cli).
#    pdftotext dicari: PATH -> salinan permanen hermes
#    (/opt/data/services/pdftotext/bin).
# ═══════════════════════════════════════════════════════════════════════
set -u

PROYEK="$(cd "$(dirname "$0")/.." && pwd)"
SKRIP="$PROYEK/template-buku-resmi/scripts"
PY=""
GAGAL=0

judul() { echo; echo "── $* ──"; }
ok()    { echo "  ✓ $*"; }
buruk() { echo "  ✗ $*"; }

# ── 0. Prasyarat ─────────────────────────────────────────────────────────
judul "0. Prasyarat (gagal = berhenti, bukan dilewati)"

# Pilih python: hormati PY_PEMERIKSA bila diset; kalau tidak, pakai
# venv deploy (/opt/data/.venv, sama seperti periksa_kode.sh) bila ada,
# lalu python3, lalu venv hermes. Yang terpilih wajib punya python-docx.
for cand in ${PY_PEMERIKSA:-} /opt/data/.venv/bin/python3 python3 /opt/hermes/.venv/bin/python3; do
    [ -n "$cand" ] || continue
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c "import docx" 2>/dev/null; then
        PY="$cand"
        break
    fi
done
if [ -z "$PY" ]; then
    buruk "tidak ada python + python-docx (dibutuhkan uji isi-nomor-toc)"
    exit 1
fi
ok "python ($PY) + python-docx ada"

if [ -n "${WORDCRAFT_CLI:-}" ] && [ -x "$WORDCRAFT_CLI" ]; then
    ok "WordCraft dari WORDCRAFT_CLI: $WORDCRAFT_CLI"
elif command -v wordcraft-cli >/dev/null 2>&1; then
    ok "WordCraft dari PATH: $(command -v wordcraft-cli)"
elif [ -x /opt/data/services/wordcraft-uji/bin/wordcraft-cli ]; then
    export WORDCRAFT_CLI=/opt/data/services/wordcraft-uji/bin/wordcraft-cli
    ok "WordCraft dari salinan hermes: $WORDCRAFT_CLI"
else
    buruk "wordcraft-cli tidak ditemukan (WORDCRAFT_CLI / PATH / hermes)"
    exit 1
fi

if command -v pdftotext >/dev/null 2>&1; then
    ok "pdftotext dari PATH: $(command -v pdftotext)"
elif [ -x /opt/data/services/pdftotext/bin/pdftotext ]; then
    export PATH="/opt/data/services/pdftotext/bin:$PATH"
    ok "pdftotext dari salinan permanen hermes"
else
    buruk "pdftotext tidak ditemukan (PATH / salinan hermes)"
    exit 1
fi

export PYTHONPATH="$SKRIP${PYTHONPATH:+:$PYTHONPATH}"

# ── Suite ────────────────────────────────────────────────────────────────
jalan() { # $1 = nama, $2 = berkas uji
    judul "$1 ($2)"
    if [ ! -f "$SKRIP/$2" ]; then
        buruk "berkas uji tidak ada: $SKRIP/$2"
        GAGAL=1
        return
    fi
    OUT="$("$PY" "$SKRIP/$2" 2>&1)"
    KODE=$?
    echo "$OUT" | tail -4 | sed 's/^/    /'
    if [ "$KODE" -ne 0 ]; then
        buruk "GAGAL — $1 (exit $KODE)"
        GAGAL=1
    elif echo "$OUT" | grep -q "^SKIP:"; then
        buruk "GAGAL — $1 dilewati (SKIP), bukan diuji"
        GAGAL=1
    else
        ok "LULUS — $1"
    fi
}

jalan "JENIS"         "uji_gerbang_jenis.py"
jalan "CHAPTER"       "uji_bergigi_v6.py"
jalan "CARI-TOC"      "uji_cari_toc.py"
jalan "ISI-NOMOR-TOC" "uji_isi_nomor_toc.py"
jalan "REGRESI-EMAS"  "uji_regresi_emas.py"

# ── Vonis ────────────────────────────────────────────────────────────────
echo
if [ "$GAGAL" -ne 0 ]; then
    echo "⛔ GERBANG BUKU GAGAL — JANGAN DEPLOY."
    echo "   Perbaiki dulu, lalu ulangi: bash scripts/periksa_buku.sh"
    exit 1
fi
echo "✅ GERBANG BUKU LULUS — mesin buku sehat, aman dilanjutkan ke deploy."
exit 0
