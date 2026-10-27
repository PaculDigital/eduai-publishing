#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  🚨 WARNING PERMANEN — PERINTAH BOS (16 Sep 2026) 🚨                     ║
# ║  "JANGAN PERNAH SEKALI KALI MENCOBA MENAMBAL JIKA ADA ERROR. HARUS       ║
# ║   ANALISA DAN TEMUKAN AKAR MASALAHNYA, DAN KEMBALI KE RUJUKAN            ║
# ║   DOKUMENTASI ATAU MASTER PLAN SEBELUMNYA."                             ║
# ║  CARA: (1) REPRODUKSI (2) UKUR pakai alat nyata (3) BUKA RUJUKAN         ║
# ║  MASTER_PLAN/dokumen dulu (4) cari AKAR bukan gejala (5) perbaiki AKAR   ║
# ║  + pasang gerbang/uji agar tak terulang.                                ║
# ║  KENAPA: tambalan benar sekarang tapi GAGAL di kasus lain.              ║
# ╚══════════════════════════════════════════════════════════════════════════╝
# ══════════════════════════════════════════════════════════════════════════
#  PERIKSA KODE EDUAI — GERBANG WAJIB SEBELUM DEPLOY
# ══════════════════════════════════════════════════════════════════════════
#  ══ KENAPA BERKAS INI ADA (akar masalah, 16Sep26) ══
#
#  INSIDEN: kode Langkah C+D+E ditulis dengan 4 NAMA YANG TIDAK ADA
#  (tulis_docx, datetime, timezone, _sidik_jari). Deploy TIDAK menolaknya:
#      → jalankan.sh hanya memeriksa (a) hash image == source,
#        (b) berkas template ada, (c) /health setelah restart.
#      → /health TETAP 200 karena FastAPI mendaftarkan rute TANPA
#        menjalankan isi fungsinya. NameError baru meledak saat user klik.
#      → Akibatnya bug HANYA ketemu setelah berjam-jam debug manual.
#
#  BUKTI TERUKUR: `pyflakes app/` menemukan keempatnya DALAM 1 DETIK,
#  biaya Rp 0. Lihat `_arsip/` untuk keluaran lengkapnya.
#
#  ══ ATURAN ══
#  Gerbang ini MENOLAK deploy (exit 1) bila ada:
#     1. galat sintaks (compileall)
#     2. "undefined name"  ← KELAS BUG yang menjatuhkan kita 16Sep26
#     3. app tidak bisa di-import / rute gagal didaftarkan
#  Temuan lain (import menganggur, variabel tak terpakai) hanya DILAPORKAN,
#  tidak menolak — supaya gerbang tidak rewel dan tetap dipercaya.
#
#  Pakai:  bash scripts/periksa_kode.sh            # periksa source
#          bash scripts/periksa_kode.sh --image TAG # periksa isi image baru
# ══════════════════════════════════════════════════════════════════════════
set -uo pipefail

PROYEK="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROYEK"

HIJAU=$'\033[0;32m'; MERAH=$'\033[0;31m'; KUNING=$'\033[0;33m'
BIRU=$'\033[0;34m'; TEBAL=$'\033[1m'; NORMAL=$'\033[0m'
ok()   { echo "  ${HIJAU}✓${NORMAL} $*"; }
bad()  { echo "  ${MERAH}✗${NORMAL} $*"; }
info() { echo "  ${BIRU}→${NORMAL} $*"; }
judul(){ echo; echo "${TEBAL}${BIRU}═══ $* ═══${NORMAL}"; }

GAGAL=0
PY="${PY_PEMERIKSA:-/opt/data/.venv/bin/python3}"

# ── 0a. Ruang kerja SEMENTARA yang unik per run ──────────────────────────
#  AKAR (27 Okt 2026): dulu semua hasil ditulis ke nama TETAP di /tmp
#  (/tmp/eduai_sintaks.txt, /tmp/g_perbaikan.log, …). Kalau sekali saja
#  skrip ini dijalankan sebagai root, berkasnya jadi milik root dan run
#  berikutnya sebagai user lain kena "Permission denied". Akibatnya:
#    • compileall gagal MENULIS → blok else jalan → "ADA GALAT SINTAKS"
#      padahal sintaksnya BERSIH (merah palsu, deploy dibatalkan).
#    • `tee /tmp/g_*.log | grep -q '0 GAGAL'` dapat masukan KOSONG →
#      hasil cek bisa merah palsu (dan hijau palsu bila pola kebetulan cocok).
#  PERBAIKAN AKAR: mktemp -d membuat direktori BARU milik user ini, jadi
#  tak mungkin bertabrakan dengan sisa run lain. Nama berkas TETAP (tanpa
#  akhiran acak) supaya isi skrip lain tidak perlu diubah.
RUANG="$(mktemp -d "${TMPDIR:-/tmp}/eduai-periksa.XXXXXXXX")" || {
    echo "  ✗ tidak bisa membuat ruang sementara di ${TMPDIR:-/tmp}" >&2
    exit 1
}
SINTAKS="$RUANG/eduai_sintaks.txt"
PYFLAKES="$RUANG/eduai_pyflakes.txt"
LOG_QC_BRIEF="$RUANG/g_qc_brief.log"
LOG_ILUSTRASI="$RUANG/g_ilustrasi.log"
LOG_SAPAAN="$RUANG/g_sapaan.log"
LOG_PERBAIKAN="$RUANG/g_perbaikan.log"
bersihkan() { rm -rf "$RUANG" 2>/dev/null || true; }
trap bersihkan EXIT INT TERM
info "ruang sementara: $RUANG"

echo "${TEBAL}PERIKSA KODE EDUAI${NORMAL} — $(date '+%d %b %Y %H:%M')"

# ── 0. Alat pemeriksa tersedia? (kalau tidak, pasang sekali) ─────────────
judul "0. Alat pemeriksa"
if [ ! -x "$PY" ]; then
    PY="$(command -v python3)"
    info "venv pemeriksa tidak ada → pakai $PY"
fi
if ! "$PY" -c "import pyflakes" 2>/dev/null; then
    info "pyflakes belum ada → memasang (uv)"
    if command -v uv >/dev/null 2>&1; then
        uv pip install --python "$PY" -q pyflakes 2>&1 | tail -1
    else
        "$PY" -m pip install -q pyflakes 2>&1 | tail -1
    fi
fi
if "$PY" -c "import pyflakes" 2>/dev/null; then
    ok "pyflakes $("$PY" -m pyflakes --version 2>&1 | head -1)"
else
    bad "pyflakes TIDAK BISA dipasang → gerbang tidak bisa jalan"
    info "pasang manual: uv pip install --python $PY pyflakes"
    exit 1
fi

# ── 1. Sintaks ───────────────────────────────────────────────────────────
judul "1. Sintaks (compileall)"
if "$PY" -m compileall -q app/ >"$SINTAKS" 2>&1; then
    ok "semua berkas .py di app/ bisa dikompilasi"
else
    bad "ADA GALAT SINTAKS:"
    sed 's/^/      /' "$SINTAKS" | head -20
    GAGAL=1
fi

# ── 2. pyflakes: PEMISAHAN KERAS vs LAPORAN ──────────────────────────────
#    "undefined name" = KERAS (kode pasti meledak saat barisnya dijalankan)
#    sisanya          = LAPORAN (bersih-bersih, tidak menolak deploy)
judul "2. pyflakes — nama tak terdefinisi (MENOLAK deploy)"
"$PY" -m pyflakes app/ >"$PYFLAKES" 2>&1
KERAS=$(grep -c "undefined name" "$PYFLAKES" || true)
if [ "$KERAS" -gt 0 ]; then
    bad "$KERAS nama TAK TERDEFINISI — kode ini akan meledak saat dipakai:"
    grep "undefined name" "$PYFLAKES" | sed 's/^/      /'
    info "Ini kelas bug yang menjatuhkan kita 16Sep26 (tulis_docx/_sidik_jari)."
    GAGAL=1
else
    ok "tidak ada nama tak terdefinisi"
fi

N_LAPOR=$(grep -vc "undefined name" "$PYFLAKES" || true)
if [ "${N_LAPOR:-0}" -gt 0 ]; then
    judul "2b. Laporan bersih-bersih (TIDAK menolak deploy)"
    head -25 "$PYFLAKES" | grep -v "undefined name" | sed 's/^/      /'
    info "$N_LAPOR temuan. Rapikan saat senggang, bukan penghalang deploy."
fi

# ── 3. Import & rute di dalam IMAGE (bukan cuma source) ──────────────────
judul "3. Import app + daftar rute"
IMAGE="${1:-}"
case "$IMAGE" in --image) IMAGE="${2:-}";; esac

if [ -n "$IMAGE" ]; then
    # Diperiksa di IMAGE BARU, sebelum container lama diganti.
    if docker image inspect "$IMAGE" >/dev/null 2>&1; then
        HASIL="$(docker run --rm --entrypoint python3 "$IMAGE" -c "
import app.main as m
print('RUTE', len(m.app.routes))
" 2>&1)"
        if echo "$HASIL" | grep -q "^RUTE"; then
            ok "image $IMAGE: app ter-import, $(echo "$HASIL" | grep '^RUTE' | awk '{print $2}') rute terdaftar"
        else
            bad "image $IMAGE GAGAL meng-import app:"
            echo "$HASIL" | tail -12 | sed 's/^/      /'
            GAGAL=1
        fi
    else
        info "image $IMAGE tidak ada — langkah ini dilewati"
    fi
else
    # ⚠️ Memeriksa SOURCE (bukan container yang jalan) — sumber kebenaran.
    # Kalau memakai `docker exec eduai-app`, yang diperiksa kode LAMA yang
    # sedang jalan → gerbang LOLOS padahal source baru masih rusak.
    #
    # ⚠️ JANGAN pakai `docker run -v $PWD/app:...` — mount TIDAK tembus:
    #    Wulan jalan DI DALAM container hermes, /opt/data = subvol
    #    /root/.hermes, BEDA dari yang dilihat Docker daemon (inode beda).
    #    Terbukti 16Sep26: mount tampak jalan tapi isinya kosong.
    #    `docker cp` TERBUKTI tembus (dipakai di mana-mana di repo ini).
    IMG_JALAN="$(docker inspect eduai-app --format '{{.Config.Image}}' 2>/dev/null || echo '')"
    if [ -z "$IMG_JALAN" ]; then
        info "container eduai-app tidak ada — langkah ini dilewati"
    else
        CT_CEK="eduai-cek-$$"
        docker rm -f "$CT_CEK" >/dev/null 2>&1 || true
        # env SAMA seperti produksi (jalankan.sh memakai --env-file .env):
        # tanpa itu app menolak start ("EDUAI_SECRET_KEY belum diset") dan
        # gerbang memberi positif-palsu. Terbukti 16Sep26.
        ENV_ARG="--env-file .env"
        [ -f .env ] || ENV_ARG=""
        docker create --name "$CT_CEK" $ENV_ARG --entrypoint python3 "$IMG_JALAN" -c "
import ast, pathlib
n = 0
for p in pathlib.Path('/app/app').rglob('*.py'):
    ast.parse(p.read_text(encoding='utf-8'))
    n += 1
print('PARSE', n)
import importlib
for nama in ('app.ai', 'app.main', 'app.proses', 'app.tulis_docx', 'app.versi'):
    try:
        importlib.import_module(nama)
        print('IMPORT-OK', nama)
    except Exception as e:
        print('IMPORT-GAGAL', nama, type(e).__name__, e)
" >/dev/null 2>&1
        # source TERBARU disalin ke dalam wadah pemeriksa
        docker cp app/. "$CT_CEK:/app/app/" >/dev/null 2>&1
        HASIL="$(docker start -a "$CT_CEK" 2>&1)"
        docker rm -f "$CT_CEK" >/dev/null 2>&1 || true

        if echo "$HASIL" | grep -q "^PARSE"; then
            ok "semua berkas .py bisa di-parse ($(echo "$HASIL" | grep '^PARSE' | awk '{print $2}') berkas)"
        else
            bad "gagal parse / app tidak bisa dijalankan:"
            echo "$HASIL" | tail -10 | sed 's|^|      |'
            GAGAL=1
        fi

        if echo "$HASIL" | grep -q "IMPORT-GAGAL"; then
            bad "modul ini GAGAL di-import (rute tidak akan terdaftar):"
            echo "$HASIL" | grep "IMPORT-GAGAL" | sed 's|^|      |'
            GAGAL=1
        else
            N="$(echo "$HASIL" | grep -c 'IMPORT-OK' || true)"
            ok "${N:-0} modul penting ter-import dari SOURCE (ai, main, proses, tulis_docx, versi)"
        fi
    fi
fi

# ── ANTI-BIKIN-BARU (06Okt26, perintah Bos) ──────────────────────────────
#  Aturan "pakai alat yang SUDAH ADA, jangan bikin baru" sudah tertulis di
#  banyak tempat TAPI Wulan tetap melanggar (3× dalam satu turn). Pelajaran
#  dari gerbang ikon: aturan tulisan TIDAK memaksa; gerbang yang bisa GAGAL
#  baru memaksa. Gerbang ini MENOLAK deploy kalau ada alat/skrip baru
#  yang dibuat padahal padanannya sudah ada.
if [ -f "_gerbang_anti_bikin_baru.py" ]; then
    echo
    echo "── ANTI-BIKIN-BARU (alat yang sudah ada, jangan bikin baru) ──"
    HASIL_AB="$(python3 _gerbang_anti_bikin_baru.py 2>&1 || true)"
    #  ⚠️ JEBAKAN: baris ringkasan "TOTAL: n LULUS / 0 GAGAL" juga memuat kata
    #     "GAGAL" — kalau digrep begitu, gerbang GAGAL PALSU. Periksa BARIS
    #     yang benar-benar bertanda GAGAL (awalnya "  GAGAL  ").
    if echo "$HASIL_AB" | grep -qE '^  GAGAL  '; then
        bad "ada alat/skrip BARU padahal padanannya SUDAH ADA:"
        echo "$HASIL_AB" | grep -E '^  GAGAL  ' | sed 's|^|      |'
        GAGAL=1
    else
        ok "tidak ada alat baru — Wulan memakai yang sudah ada"
    fi
fi

# ── SETELAN PRODUKSI (alat uji wajib sama dengan produksi) ────────────────
#  KENAPA (akar, 15Okt26): alat uji `_hakim_mentah.py` ditulis 24 Sep SEBELUM
#  keputusan `enable_thinking: False` (29 Sep) ⇒ dia TIDAK ikut diperbarui ⇒
#  AI berpikir → jatah token habis → `content` KOSONG → Wulan melapor "mutu
#  POTONG buruk" padahal PRODUKSInya sehat dan ALAT UKURNYA yang rusak.
#  Aturan tertulis TIDAK cukup — gerbang yang bisa GAGAL baru memaksa.
if [ -f "_gerbang_setelan_produksi.py" ]; then
    echo
    echo "── SETELAN PRODUKSI (reasoning mati · alat uji = produksi) ──"
    HASIL_SP="$(python3 _gerbang_setelan_produksi.py 2>&1 || true)"
    if echo "$HASIL_SP" | grep -qE '^  ❌ '; then
        bad "ada alat uji yang TIDAK memakai setelan produksi:"
        echo "$HASIL_SP" | grep -E '^  ❌ |^        ⚠️ ' | sed 's|^|      |'
        GAGAL=1
    else
        ok "semua alat uji memakai setelan produksi (reasoning mati)"
    fi
fi

# ── TIKET LOLOS (Lapis 3) ────────────────────────────────────────────────
#  Menjaga: arah aman (Jev mati ⇒ tiket BATAL), elemen tanpa tiket tetap
#  ditanyakan, dan harga 2/3/5 tidak berubah diam-diam (+ elemen Done).
#  ⚠️ Dijalankan dari HOST seperti gerbang lain — jangan `docker exec`
#     ke container (kode di container bisa BEDA dari source).
if [ -f "_gerbang_porsi_alat.py" ]; then
    echo
    echo "── PORSI ALAT (ID dokumen → Jev/Hakim · 19 Okt 2026) ──"
    HASIL_PA="$(PYTHONPATH="$PROYEK" EDUAI_APP_DIR="$PROYEK" "$PY" _gerbang_porsi_alat.py 2>&1)"
    echo "$HASIL_PA" | tail -3
    echo "$HASIL_PA" | grep -q "0 GAGAL" || GAGAL=1
fi

if [ -f "_gerbang_salinan_mesin.py" ]; then
    echo
    echo "── SALINAN MESIN BUKU (host ↔ proyek identik · 19 Okt 2026) ──"
    HASIL_SM="$(PYTHONPATH="$PROYEK" EDUAI_APP_DIR="$PROYEK" "$PY" _gerbang_salinan_mesin.py 2>&1)"
    echo "$HASIL_SM" | tail -3
    echo "$HASIL_SM" | grep -q "0 GAGAL" || GAGAL=1
fi

#  MODUL MESIN BUKU HARUS BISA DIIMPOR DARI DALAM IMAGE (20 Okt 2026).
#  AKAR TERUKUR: `jev_buku_umum.py`, `diagram_buku.py`, `tata_paragraf.py`
#  TIDAK PERNAH di-COPY Dockerfile ⇒ di container `ModuleNotFoundError`,
#  tetapi SEMUA gerbang di host tetap HIJAU karena berkasnya ada di host.
#  Cacat SENYAP: perakit jatuh ke jalur regex lama, buku tetap terbit tanpa
#  Jev & tanpa 8 bentuk diagram. Gerbang ini menanyakan LANGSUNG ke IMAGE.
#
#  ⚠️ DIPINDAH KE LANGKAH 4 `jalankan.sh` (20 Okt 2026, terukur): gerbang ini
#  TIDAK BISA dinilai di Langkah 0 karena image-nya belum dibangun. Saat di
#  Langkah 0 ia membaca container HIDUP berisi image LAMA ⇒ deploy dibatalkan
#  padahal image baru sehat. Di jalankan.sh ia dijalankan setelah `docker build`.
#
#  ⚠️ DI SINI DILEWATI — dan itu SENGAJA: bukan gerbang hiasan, karena
#  `jalankan.sh` LANGKAH 4 WAJIB menjalankannya (`exit 1` bila gagal).
#  Kalau `EDUAI_IMAGE_UJI` terisi (dipanggil manual dengan tag), JalANkan.
if [ -n "${EDUAI_IMAGE_UJI:-}" ] && [ -f "$PROYEK/gerbang_modul_di_image.py" ]; then
    echo
    echo "── MODUL MESIN BUKU BISA DIIMPOR DARI IMAGE (20 Okt 2026) ──"
    HASIL_MI="$(EDUAI_IMAGE_UJI="$EDUAI_IMAGE_UJI" "$PY" "$PROYEK/gerbang_modul_di_image.py" 2>&1)"
    echo "$HASIL_MI" | tail -3
    echo "$HASIL_MI" | grep -q '"gagal": 0' || GAGAL=1
fi

#  RINGKASAN BAB (19 Okt 2026) — ringkasan bab DISUSUN dari ringkasan sub-bab,
#  bukan panggil AI ulang. AI dipalsukan (Rp 0, tanpa jaringan) ⇒ jalan di host.
if [ -f "$PROYEK/_gerbang_ringkasan_bab.py" ]; then
    echo
    echo "── RINGKASAN BAB (0 panggilan AI · 19 Okt 2026) ──"
    HASIL_RB="$(PYTHONPATH="$PROYEK" EDUAI_APP_DIR="$PROYEK" "$PY" "$PROYEK/_gerbang_ringkasan_bab.py" 2>&1)"
    echo "$HASIL_RB" | grep -E "LULUS / " | tail -1
    echo "$HASIL_RB" | grep -q "0 GAGAL" || GAGAL=1
fi

#  QC BRIEF ILUSTRASI DUA BAHASA + ILUSTRASI TIDAK DIBUANG (19 Okt 2026).
#  AI dipalsukan ⇒ jalan di host, Rp 0.
if [ -f "$PROYEK/_gerbang_qc_brief_dua_bahasa.py" ]; then
    echo
    echo "── QC BRIEF DUA BAHASA (19 Okt 2026) ──"
    if /opt/data/.venv/bin/python "$PROYEK/_gerbang_qc_brief_dua_bahasa.py" 2>&1 | tee "$LOG_QC_BRIEF" | grep -qE "0 GAGAL"; then
        grep -E "LULUS /" "$LOG_QC_BRIEF" | tail -1
    else
        echo "  ✗ GAGAL — QC brief dua bahasa tidak lulus"; tail -20 "$LOG_QC_BRIEF"; GAGAL=$((GAGAL+1))
    fi
fi

if [ -f "$PROYEK/_gerbang_ilustrasi_tak_dibuang.py" ]; then
    echo
    echo "── ILUSTRASI TIDAK DIBUANG (19 Okt 2026) ──"
    if /opt/data/.venv/bin/python "$PROYEK/_gerbang_ilustrasi_tak_dibuang.py" 2>&1 | tee "$LOG_ILUSTRASI" | grep -qE "0 GAGAL"; then
        grep -E "LULUS /" "$LOG_ILUSTRASI" | tail -1
    else
        echo "  ✗ GAGAL — ilustrasi bisa dibuang lagi"; tail -20 "$LOG_ILUSTRASI"; GAGAL=$((GAGAL+1))
    fi
fi

#  SAPAAN PER JENIS BUKU (20 Okt 2026). Rp 0.
if [ -f "$PROYEK/_gerbang_sapaan_jenis.py" ]; then
    echo
    echo "── SAPAAN PER JENIS BUKU (20 Okt 2026) ──"
    if /opt/data/.venv/bin/python "$PROYEK/_gerbang_sapaan_jenis.py" 2>&1 | tee "$LOG_SAPAAN" | grep -qE "0 GAGAL"; then
        grep -E "LULUS /" "$LOG_SAPAAN" | tail -1
    else
        echo "  ✗ GAGAL — sapaan jenis buku bocor"; tail -20 "$LOG_SAPAAN"; GAGAL=$((GAGAL+1))
    fi
fi

#  PERBAIKAN-OTOMATIS BAB BERMASALAH (Lapis 3c-2 · 19-20 Okt 2026).
#  AI dipalsukan ⇒ jalan di host, Rp 0.
if [ -f "$PROYEK/_gerbang_perbaikan_bab.py" ]; then
    echo
    echo "── PERBAIKAN BAB BERMASALAH (19-20 Okt 2026) ──"
    if /opt/data/.venv/bin/python "$PROYEK/_gerbang_perbaikan_bab.py" 2>&1 | tee "$LOG_PERBAIKAN" | grep -qE "0 GAGAL"; then
        grep -E "LULUS /" "$LOG_PERBAIKAN" | tail -1
    else
        echo "  ✗ GAGAL — perbaikan bab bermasalah tidak lulus"; tail -20 "$LOG_PERBAIKAN"; GAGAL=$((GAGAL+1))
    fi
fi

#  MUTU ISI BUKU (Lapis 3c · 19 Okt 2026). AI dipalsukan ⇒ jalan di host, Rp 0.
if [ -f "$PROYEK/_gerbang_mutu_isi_buku.py" ]; then
    echo
    echo "── MUTU ISI BUKU (penjaga isi berulang · 19 Okt 2026) ──"
    HASIL_MI="$(PYTHONPATH="$PROYEK" EDUAI_APP_DIR="$PROYEK" "$PY" "$PROYEK/_gerbang_mutu_isi_buku.py" 2>&1)"
    echo "$HASIL_MI" | grep -E "LULUS / " | tail -1
    echo "$HASIL_MI" | grep -q "0 GAGAL" || GAGAL=1
fi

#  LAPIS 3 — BAB BERSAMAAN (19 Okt 2026). AI dipalsukan ⇒ jalan di host, Rp 0.
if [ -f "$PROYEK/_gerbang_lapis3_bab_bersamaan.py" ]; then
    echo
    echo "── LAPIS 3 (bab bersamaan · 19 Okt 2026) ──"
    HASIL_L3="$(PYTHONPATH="$PROYEK" EDUAI_APP_DIR="$PROYEK" "$PY" "$PROYEK/_gerbang_lapis3_bab_bersamaan.py" 2>&1)"
    echo "$HASIL_L3" | grep -E "LULUS / " | tail -1
    echo "$HASIL_L3" | grep -q "0 GAGAL" || GAGAL=1
fi

#  BUKU LATAR (19 Okt 2026) — butuh fastapi, jadi DIJALANKAN DI DALAM IMAGE,
#  bukan di host. Memakai image terakhir yang berhasil dibangun.
if [ -f "_gerbang_buku_latar.py" ]; then
    echo
    echo "── BUKU LATAR (titip pekerjaan · 19 Okt 2026) ──"
    #  ⚠️ JEBAKAN 19 Okt: gerbang ini DILEWATI DIAM-DIAM kalau image kosong,
    #     lalu `periksa_kode.sh` tetap LULUS — gerbang hiasan. Sekarang:
    #     tidak ada image = GAGAL, bukan lewat.
    IMG_UJI="$IMAGE"
    if [ -z "$IMG_UJI" ] || ! docker image inspect "$IMG_UJI" >/dev/null 2>&1; then
        IMG_UJI="$(docker images --format '{{.Repository}}:{{.Tag}}' \
                   | grep '^eduai-app:' | grep -v cadangan | head -1)"
    fi
    if [ -z "$IMG_UJI" ]; then
        echo "  ❌ tidak ada image untuk menjalankan gerbang — build dulu"
        GAGAL=1
    else
        echo "  (image uji: $IMG_UJI)"
        HASIL_BL="$(docker run --rm --entrypoint python -w /app \
            -e EDUAI_SECRET_KEY=uji -e EDUAI_OO_JWT_SECRET=uji \
            -e EDUAI_ROUTER_KEY=uji -i "$IMG_UJI" \
            - < _gerbang_buku_latar.py 2>&1)"
        echo "$HASIL_BL" | tail -3
        echo "$HASIL_BL" | grep -q "0 GAGAL" || GAGAL=1
    fi
fi

if [ -f "_uji_id_buku_ke_alat.py" ]; then
    echo
    echo "── ID BUKU → ALAT (19 Okt 2026) ──"
    HASIL_IB="$(PYTHONPATH="$PROYEK" EDUAI_APP_DIR="$PROYEK" "$PY" _uji_id_buku_ke_alat.py 2>&1)"
    echo "$HASIL_IB" | tail -3
    echo "$HASIL_IB" | grep -q "0 GAGAL" || GAGAL=1
fi

if [ -f "_gerbang_tiket_lolos.py" ]; then
    echo
    echo "── TIKET LOLOS (Lapis 3 · 16 Okt 2026) ──"
    HASIL_TL="$(PYTHONPATH="$PROYEK" EDUAI_APP_DIR="$PROYEK" "$PY" _gerbang_tiket_lolos.py 2>&1 || true)"
    if echo "$HASIL_TL" | grep -qE '^  ❌ '; then
        bad "gerbang tiket lolos GAGAL:"
        echo "$HASIL_TL" | grep -E '^  ❌ |HASIL:' | sed 's|^|      |'
        GAGAL=1
    else
        ok "$(echo "$HASIL_TL" | grep -E 'HASIL:' | sed 's|^ *||')"
    fi
fi

# ── PORSI ALAT (ID dokumen menentukan Jev/Hakim · 19 Okt 2026) ───────────
#  Perintah Bos: "harus punya id sendiri ... agar menggunakan jev dan hakim
#  tepat dan tidak salah alat". Gerbang ini MENOLAK deploy kalau:
#    · buku dikirim ke Jev/Hakim, atau
#    · skripsi/tesis/artikel kehilangan Jev/Hakim, atau
#    · ID tak dikenal mulai MENEBak alat (fail-safe bocor).
if [ -f "_gerbang_porsi_alat.py" ]; then
    echo
    echo "── PORSI ALAT (ID dokumen → Jev/Hakim · 19 Okt 2026) ──"
    HASIL_PA="$(PYTHONPATH="$PROYEK" "$PY" _gerbang_porsi_alat.py 2>&1 || true)"
    if echo "$HASIL_PA" | grep -qE '^  ❌ '; then
        bad "gerbang porsi alat GAGAL:"
        echo "$HASIL_PA" | grep -E '^  ❌ |PORSI ALAT:' | sed 's|^|      |'
        GAGAL=1
    else
        ok "$(echo "$HASIL_PA" | grep -E 'PORSI ALAT:' | sed 's|^ *||')"
    fi
fi

if [ -f "_uji_id_buku_ke_alat.py" ]; then
    echo
    echo "── ID BUKU → ALAT (sambungan rute /buku/susun) ──"
    HASIL_IB="$(PYTHONPATH="$PROYEK" "$PY" _uji_id_buku_ke_alat.py 2>&1 || true)"
    if echo "$HASIL_IB" | grep -qE '^  ❌ '; then
        bad "uji sambungan ID buku GAGAL:"
        echo "$HASIL_IB" | grep -E '^  ❌ |ID BUKU' | sed 's|^|      |'
        GAGAL=1
    else
        ok "$(echo "$HASIL_IB" | grep -E 'ID BUKU' | sed 's|^ *||')"
    fi
fi

# ── KESIMPULAN ───────────────────────────────────────────────────────────
echo
if [ "$GAGAL" -ne 0 ]; then
    echo "${MERAH}${TEBAL}⛔ PERIKSA KODE GAGAL — JANGAN DEPLOY.${NORMAL}"
    echo "   Perbaiki dulu, lalu ulangi: ${TEBAL}bash scripts/periksa_kode.sh${NORMAL}"
    exit 1
fi
echo "${HIJAU}${TEBAL}✅ PERIKSA KODE LULUS — aman dilanjutkan ke build.${NORMAL}"
echo
exit 0
