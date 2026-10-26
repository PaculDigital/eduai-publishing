#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  🚨 WARNING PERMANEN — PERINTAH BOS (16 Sep 2026) 🚨                     ║
# ║                                                                          ║
# ║  "JANGAN PERNAH SEKALI KALI MENCOBA MENAMBAL JIKA ADA ERROR.            ║
# ║   HARUS ANALISA DAN TEMUKAN AKAR MASALAHNYA, DAN KEMBALI KE RUJUKAN     ║
# ║   DOKUMENTASI ATAU MASTER PLAN SEBELUMNYA."                            ║
# ║                                                                          ║
# ║  CARA KERJA WAJIB (jangan dilanggar):                                    ║
# ║   1. REPRODUKSI error dulu — jangan menebak.                             ║
# ║   2. UKUR: pakai alat ukur nyata (pyflakes, grep SELURUH repo, log).     ║
# ║   3. BUKA RUJUKAN: SOT.md / docs/sot/ / skill ini dulu.                 ║
# ║   4. Cari AKAR (kenapa ini bisa terjadi), bukan gejala.                  ║
# ║   5. Perbaiki AKAR-nya + TULIS gerbang/uji supaya tak terulang.          ║
# ║                                                                          ║
# ║  KENAPA: tambalan "benar sekarang" tapi GAGAL di kasus lain.             ║
# ║  BUKTI: 4 tambalan daftar-isi GAGAL → 1 aturan akar awal_isi_naskah().  ║
# ╚══════════════════════════════════════════════════════════════════════════╝
# ═══════════════════════════════════════════════════════════════════════
#  jalankan.sh — DEPLOY EduAi Publishing (SATU ARAH / SOT)
# ═══════════════════════════════════════════════════════════════════════
#  PRINSIP SOT (ACC Bos 15Sep26):
#    SATU sumber kebenaran = SOURCE di disk (`app/`, `prompts/`).
#    Alur WAJIB satu arah, tidak boleh dibalik:
#
#        SOURCE (app/) → BUILD IMAGE → CEK IMAGE → VERIFIKASI ISI → RUN
#
#  DILARANG (pelanggaran SOT yang terbukti 15Sep26):
#    ✗ `docker cp app/... eduai-app:/app/...`  → bikin image BOHONG
#      (image 13Sep tapi isi 15Sep; 45 file hanya ada di container,
#       hilang total kalau container di-run ulang dari image)
#    ✗ Edit file langsung di dalam container (perubahan tidak kembali
#      ke disk → hilang saat container diganti)
#
#  ATURAN DATA (bedakan kode vs data):
#    • KODE   = di-bake ke image lewat `COPY app ./app` (BAKU, reproducible)
#    • DATA   = bind-mount (eduai.db, uploads) — KHUSUS, tidak di-bake
#    Data SELALU dibaca/tulis lewat `docker exec` / `docker cp`,
#    JANGAN lewat `/opt/data` sisi Hermes (inode BEDA — terbukti 15Sep26).
#
#  CARA PAKAI:
#    bash jalankan.sh              → deploy + verifikasi
#    bash jalankan.sh --dry        → cek saja, tidak menyentuh container
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Konfigurasi ────────────────────────────────────────────────────────
PROYEK="/opt/data/services/eduai-publishing"
NAMA_CONTAINER="eduai-app"
PORT_HOST="127.0.0.1:8100"
PORT_APP="8000"
IMAGE_BASE="eduai-app"
TAG="$(date +%Y%m%d_%H%M%S)-sot"
ENV_FILE="$PROYEK/.env"
DRY=0
[ "${1:-}" = "--dry" ] && DRY=1

cd "$PROYEK"

echo "═══════════════════════════════════════════════════════════════"
echo "  DEPLOY EduAi — alur SOT satu arah"
echo "  Proyek : $PROYEK"
echo "  Tag    : $IMAGE_BASE:$TAG"
echo "  Mode   : $([ $DRY -eq 1 ] && echo 'DRY-RUN (tidak mengubah apa pun)' || echo 'LIVE')"
echo "═══════════════════════════════════════════════════════════════"

# ── LANGKAH 0: Pastikan source bersih & lengkap ────────────────────────
echo
echo "── [0/5] Periksa source ────────────────────────────────────────"
[ -f Dockerfile ] || { echo "❌ Dockerfile tidak ada"; exit 1; }
[ -f requirements.txt ] || { echo "❌ requirements.txt tidak ada"; exit 1; }
[ -d app ] || { echo "❌ folder app/ tidak ada"; exit 1; }
[ -f app/main.py ] || { echo "❌ app/main.py tidak ada"; exit 1; }

# Aset WAJIB (dirujuk kode) — cek sebelum build biar tidak gagal di tengah
for aset in app/static/eduai.css app/static/logo-96.png app/static/hero-bg.svg; do
  [ -f "$aset" ] || { echo "❌ aset wajib hilang: $aset"; exit 1; }
done
echo "  ✅ Source lengkap ($(find app -name '*.py' | wc -l) file .py, $(find app/templates -type f | wc -l) template)"
echo "  ✅ Aset wajib ada"

if [ $DRY -eq 1 ]; then
  echo
  echo "  DRY-RUN selesai — source sehat, siap deploy."
  echo "  Jalankan tanpa --dry untuk benar-benar deploy."
  exit 0
fi

# ── LANGKAH 0: PERIKSA KODE (GERBANG WAJIB — 16Sep26) ──────────────────
# ══ KENAPA DITARUH PALING DEPAN (akar masalah, bukan tambalan) ══════════
# 16Sep26 kode Langkah C+D+E ditulis dengan 4 NAMA TAK TERDEFINISI
# (tulis_docx, datetime, timezone, _sidik_jari). Semua gerbang lama LOLOS:
#   • `docker build`        → sukses (Python tidak dijalankan saat build)
#   • hash image == source  → cocok (isinya memang sama, sama-sama rusak)
#   • berkas template ada   → ada
#   • /health setelah restart → 200, SEHAT! (FastAPI mendaftarkan rute
#     TANPA menjalankan isi fungsinya; NameError baru meledak saat user klik)
# Jadi deploy "sukses" padahal fitur mati. Akarnya: TIDAK ADA gerbang yang
# memeriksa KESEHATAN KODE, hanya KEUTUHAN BERKAS.
# ═══════════════════════════════════════════════════════════════════════
echo
echo "── [0/5] PERIKSA KODE (gerbang wajib) ────────────────────────"
if ! bash scripts/periksa_kode.sh; then
  echo
  echo "⛔ DEPLOY DIBATALKAN — kode belum sehat."
  echo "   Tidak ada yang diubah: image lama masih jalan, DB tidak disentuh."
  echo "   Perbaiki temuan di atas, lalu jalankan lagi: bash jalankan.sh"
  exit 1
fi

# ── LANGKAH 0b: GERBANG EDITOR (secure_link → -4) ──────────────────────
#  AKAR TERUKUR 30Sep26: kunci `secure_link` BEDA (ds.conf vs local.json)
#  → nginx 403 pada Editor.bin → editor "errorCode:-4 Unduhan gagal".
#  Kunci ditulis ULANG acak saat oo-converter boot. Pagar lama hanya ada
#  di jalankan_oo.sh §5a — MELEWAT kalau OO dibuat ulang dengan cara lain.
#  Gerbang ini memeriksa dari LUAR & menyebut OBATNYA.
echo
echo "── [0b/5] GERBANG EDITOR (kunci secure_link + Editor.bin) ────"
if ! bash scripts/periksa_editor.sh; then
  echo
  echo "⚠️  PERINGATAN: gerbang editor GAGAL."
  echo "   OBAT: bash scripts/perbaiki_oo.sh   (menyamakan kunci + reload nginx)"
  echo "   Lalu ulangi: bash scripts/periksa_editor.sh"
  echo
  echo "   Deploy app TIDAK dibatalkan (kode app tidak bersalah), TETAPI"
  echo "   editor akan tetap -4 sampai obat di atas dijalankan."
fi

# ── LANGKAH 1: Backup image lama (titik mundur) ─────────────────────────
echo
echo "── [1/5] Backup image yang sedang jalan ───────────────────────"
IMAGE_LAMA="$(docker inspect "$NAMA_CONTAINER" --format '{{.Config.Image}}' 2>/dev/null || echo '')"
if [ -n "$IMAGE_LAMA" ]; then
  echo "  Image lama: $IMAGE_LAMA"
  echo "  → backup diberi tag: ${IMAGE_BASE}:cadangan-pra-sot"
  docker tag "$IMAGE_LAMA" "${IMAGE_BASE}:cadangan-pra-sot" 2>/dev/null || true
else
  echo "  ⚠️  Container belum ada / tidak jalan — tidak ada image untuk di-backup"
fi

# ── LANGKAH 2: BACKUP DB (sebelum sentuh container!) ───────────────────
echo
echo "── [2/5] Backup DB (checkpoint WAL → docker cp → verifikasi) ──"
if docker ps --format '{{.Names}}' | grep -qx "$NAMA_CONTAINER"; then
  DIR="_arsip/pra-sot/$TAG"
  mkdir -p "$DIR"
  docker exec "$NAMA_CONTAINER" /usr/local/bin/python -c "
import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
c.close()
print('  ✅ checkpoint WAL OK')
"
  docker cp "$NAMA_CONTAINER:/app/data/eduai.db"     "$DIR/eduai.db"
  docker cp "$NAMA_CONTAINER:/app/data/eduai.db-wal" "$DIR/eduai.db-wal" 2>/dev/null || true
  docker cp "$NAMA_CONTAINER:/app/data/eduai.db-shm" "$DIR/eduai.db-shm" 2>/dev/null || true

  # VERIFIKASI backup benar-benar berisi (bukan file kosong/rusak)
  /opt/data/.venv/bin/python3 - "$DIR/eduai.db" <<'PY'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
tabel = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print(f"  ✅ Backup terverifikasi: {len(tabel)} tabel")
for t in ('users', 'files', 'transaksi'):
    if t in tabel:
        n = c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        print(f"     {t:12s}: {n}")
c.close()
PY
else
  echo "  ⚠️  Container tidak jalan — backup DB dilewati"
  DIR=""
fi

# ── LANGKAH 3: BUILD dari SOURCE (sumber kebenaran) ────────────────────
echo
echo "── [3/5] BUILD image dari source ──────────────────────────────"
docker build -t "${IMAGE_BASE}:${TAG}" -t "${IMAGE_BASE}:terbaru" .
echo "  ✅ Build selesai: ${IMAGE_BASE}:${TAG}"

# ── LANGKAH 4: VERIFIKASI ISI IMAGE (bukan cuma percaya "build sukses") ─
echo
echo "── [4/5] VERIFIKASI ISI IMAGE ─────────────────────────────────"
GAGAL=0

# 4a. Image benar-benar ada
docker image inspect "${IMAGE_BASE}:${TAG}" >/dev/null 2>&1 || { echo "  ❌ image tidak ada"; exit 1; }
echo "  ✅ Image ada di daemon"

# 4a-bis. MODUL MESIN BUKU BISA DIIMPOR DARI IMAGE (20 Okt 2026, TERUKUR).
#  AKAR: `jev_buku_umum.py`, `diagram_buku.py`, `tata_paragraf.py` tidak pernah
#  di-COPY Dockerfile ⇒ `ModuleNotFoundError` di container, TAPI semua gerbang
#  HIJAU karena dijalankan di host. Gerbang ini DI SINI (bukan Langkah 0)
#  karena baru sekarang image-nya ada. GAGAL ⇒ JANGAN ganti container.
if [ -f "gerbang_modul_di_image.py" ]; then
  echo "  Memeriksa modul mesin buku bisa diimpor dari dalam image:"
  HASIL_MI="$(EDUAI_IMAGE_UJI="${IMAGE_BASE}:${TAG}" python3 gerbang_modul_di_image.py 2>&1)"
  echo "$HASIL_MI" | grep -E '^  (✅|❌)' | head -20
  if ! echo "$HASIL_MI" | grep -q '"gagal": 0'; then
    echo
    echo "  ❌ GERBANG MODUL GAGAL — image ini akan kehilangan mesin buku."
    echo "$HASIL_MI" | grep '❌' | head -10
    echo "  ⛔ DEPLOY DIBATALKAN sebelum ganti container."
    exit 1
  fi
  echo "  ✅ Semua modul mesin buku bisa diimpor dari IMAGE"
fi

# 4b. File kunci ada di dalam image & hash-nya SAMA dengan source
echo "  Membandingkan isi image vs source:"
docker run --rm --entrypoint sh "${IMAGE_BASE}:${TAG}" -c \
  "cd /app && find app -type f -name '*.py' -exec md5sum {} \;" | sort -k2 > /tmp/sot_image.txt
find app -type f -name '*.py' -exec md5sum {} \; | sort -k2 > /tmp/sot_source.txt

N_IMG=$(wc -l < /tmp/sot_image.txt)
N_SRC=$(wc -l < /tmp/sot_source.txt)
echo "     file .py di image  : $N_IMG"
echo "     file .py di source : $N_SRC"

if [ "$N_IMG" != "$N_SRC" ]; then
  echo "  ❌ JUMLAH FILE BEDA — image tidak lengkap!"
  diff /tmp/sot_image.txt /tmp/sot_source.txt | head -20
  GAGAL=1
elif ! diff -q /tmp/sot_image.txt /tmp/sot_source.txt >/dev/null; then
  echo "  ❌ ISI BERBEDA — ada file di image yang tidak sesuai source!"
  diff /tmp/sot_image.txt /tmp/sot_source.txt | head -20
  GAGAL=1
else
  echo "  ✅ SEMUA $N_IMG file .py IDENTIK dengan source"
fi

# 4c. Template & aset kritis
for f in app/templates/masuk.html app/templates/sampah.html app/static/ikon/lucide.svg; do
  if docker run --rm --entrypoint sh "${IMAGE_BASE}:${TAG}" -c "[ -f /app/$f ]" 2>/dev/null; then
    echo "  ✅ $f ada di image"
  else
    echo "  ❌ $f HILANG dari image"
    GAGAL=1
  fi
done

if [ $GAGAL -ne 0 ]; then
  echo
  echo "  ⛔ VERIFIKASI GAGAL — container TIDAK di-restart."
  echo "     Image lama masih jalan. Perbaiki source, lalu jalankan ulang."
  exit 1
fi

# ── LANGKAH 5: GANTI CONTAINER ─────────────────────────────────────────
echo
echo "── [5/5] Ganti container ───────────────────────────────────────"
docker rm -f "$NAMA_CONTAINER" >/dev/null 2>&1 || true

# DATA: bind-mount (khusus data, TIDAK di-bake). Path di sini adalah path
# yang dilihat Docker daemon = benar. Kalau file .env ada, pakai --env-file.
ENV_ARG=""
[ -f "$ENV_FILE" ] && ENV_ARG="--env-file $ENV_FILE"

# 🔌 NAMA UNTUK 9ROUTER (17Sep26, ACC Bos) — JANGAN pakai IP mentah.
#    MASALAH: 9router berjalan dengan NetworkMode=host → TIDAK punya DNS
#    Docker, jadi nama container "9router" TIDAK bisa di-resolve dari
#    eduai-net. IP 172.17.0.1 (gateway docker0) hidup hari ini, tapi
#    Docker bisa mengubah alokasi jaringan saat restart/redeploy →
#    Errno 111 → HTTP 502 (terbukti 16Sep26 pada oo-converter .7→.4).
#    SOLUSI: --add-host menulis entri /etc/hosts di container, mengikat
#    NAMA STABIL (9router) ke gateway host. Nama tetap, IP boleh berubah.
#    Kalau gateway berubah, cukup perbarui HOST_GATEWAY di bawah.
HOST_GATEWAY=$(docker network inspect bridge --format '{{(index .IPAM.Config 0).Gateway}}' 2>/dev/null)
[ -z "$HOST_GATEWAY" ] && HOST_GATEWAY="172.17.0.1"
ALIAS_9ROUTER="${NAMA_9ROUTER:-9router}"
echo "  Alias untuk 9router: ${ALIAS_9ROUTER} → ${HOST_GATEWAY}"

docker run -d \
  --name "$NAMA_CONTAINER" \
  --restart unless-stopped \
  --network eduai-net \
  --add-host "${ALIAS_9ROUTER}:${HOST_GATEWAY}" \
  -p "$PORT_HOST:$PORT_APP" \
  -v "$PROYEK/data:/app/data" \
  -v "$PROYEK/uploads:/app/uploads" \
  -e "IMAGE_TAG=${IMAGE_BASE}:${TAG}" \
  $ENV_ARG \
  "${IMAGE_BASE}:${TAG}" >/dev/null
echo "  ✅ Container dijalankan dari ${IMAGE_BASE}:${TAG}"
#  ══════════════════════════════════════════════════════════════════════════
#  🔑 PEMERIKSA KUNCI MESIN PENCARI (12 Okt 2026)
#  PUTUSAN BOS: "Semua pencarian yang pakai apikey wajib jelas kuncinya.
#  Scopus dan openalex. Apikey wajib jelas. Bukan diam diam."
#  ⇒ Setiap deploy melaporkan kunci APA SAJA yang hidup/mati.
#  Kunci TIDAK ditaruh di sini — dibaca dari `.env` (pola sama dgn
#  EDUAI_ROUTER_KEY / PAKASIR_API_KEY) lewat `--env-file`.
#  ══════════════════════════════════════════════════════════════════════════
echo ""
echo "  ── 🔑 KUNCI MESIN PENCARI (dari .env) ──"
for _k in SCOPUS OPENALEX; do
  _banyak=$(docker exec "$NAMA_CONTAINER" python3 -c "
import os
print(len(os.getenv('EDUAI_${_k}_KEY') or ''))
" 2>/dev/null)
  if [ "${_banyak:-0}" -gt 0 ] 2>/dev/null; then
    echo "     ✅ ${_k}: AKTIF (${_banyak} karakter, terbaca dari container)"
  else
    echo "     ❌ ${_k}: KOSONG — mesin ini akan DILEWATI (cek EDUAI_${_k}_KEY di .env)"
  fi
done
#  🔑 SCITE (13Okt26) — untuk DAFTAR artikel pendukung/pembantah + kutipan.
#  Endpoint publik gratis hanya memberi ANGKA; daftar butuh token ini.
#  Lapor apa adanya (PUTUSAN BOS: "apikey wajib jelas, bukan diam-diam").
_bs=$(docker exec "$NAMA_CONTAINER" python3 -c "
import os
print(len(os.getenv('EDUAI_SCITE_TOKEN') or ''))
" 2>/dev/null)
if [ "${_bs:-0}" -gt 0 ] 2>/dev/null; then
  echo "     ✅ SCITE: AKTIF (${_bs} karakter) — angka + DAFTAR pendukung/pembantah"
else
  echo "     ❌ SCITE: KOSONG — hanya angka dasar yang tampil (perbarui EDUAI_SCITE_TOKEN di .env)"
fi
#  CATATAN (06 Okt 2026): `-e IMAGE_TAG` dititipkan supaya `sot.py` bisa
#  membaca tag image DARI DALAM container (di dalam container tidak ada
#  `docker`), tanpa perlu menebak. Dipakai gerbang `_gerbang_sot.py`.
echo "${IMAGE_BASE}:${TAG}" > "$PROYEK/IMAGE_TAG.txt" 2>/dev/null || true

# ── PAGAR 30Sep26 — JARINGAN & ONLYOFFICE (jangan dihapus) ──────────────
#  AKAR TERUKUR 30Sep26: `docker run` cuma menerima SATU --network, jadi
#  memakai `--network eduai-net` MENGESAMPINGKAN `bridge`. Dua hal diperiksa:
#   (1) app HARUS bisa menyelesaikan nama `oo-converter` (DNS eduai-net)
#       → tanpa ini `/oo/aset` = 502 → editor dokumen MATI.
#       (Insiden 30Sep26 00:59–05:40 = jaringan hilang setelah container
#        dibuat ulang; user asli kena "Editor tidak bisa dimuat".)
#   (2) `bridge` DIPERIKSA tapi TIDAK dipaksa: ingress tunnel eduai
#       memakai `http://localhost:8100` (port mapping), BUKAN IP container
#       (terverifikasi 30Sep26 lewat API Cloudflare). Jadi `bridge` tidak
#       wajib — tapi kalau ada ingress berbasis-IP, tanpa bridge = 502.
#       Karena itu: kalau bridge tidak ada, DISAMBUNG (murah, idempoten).
docker network connect bridge "$NAMA_CONTAINER" 2>/dev/null || true

echo "  Menunggu sehat..."
SEHAT=0
for i in $(seq 1 30); do
  if docker exec "$NAMA_CONTAINER" sh -c \
      "python3 -c \"import urllib.request;urllib.request.urlopen('http://localhost:8000/health',timeout=3)\"" \
      >/dev/null 2>&1; then
    SEHAT=1
    echo "  ✅ /health OK setelah ${i} detik"
    break
  fi
  sleep 1
done

if [ $SEHAT -eq 0 ]; then
  echo "  ❌ Container tidak sehat dalam 30 detik!"
  echo "  ── 30 baris log terakhir ──"
  docker logs --tail 30 "$NAMA_CONTAINER"
  echo
  echo "  BALIK KE IMAGE LAMA:"
  echo "    docker rm -f $NAMA_CONTAINER"
  echo "    docker run -d --name $NAMA_CONTAINER -p $PORT_HOST:$PORT_APP \\"
  echo "      -v $PROYEK/data:/app/data -v $PROYEK/uploads:/app/uploads \\"
  echo "      ${IMAGE_BASE}:cadangan-pra-sot"
  exit 1
fi

# ── VERIFIKASI AKHIR: kode di CONTAINER = source ───────────────────────
echo
echo "── Verifikasi akhir: container vs source ───────────────────────"
docker exec "$NAMA_CONTAINER" sh -c \
  "cd /app && find app -type f -name '*.py' -exec md5sum {} \;" | sort -k2 > /tmp/sot_jalan.txt
if diff -q /tmp/sot_jalan.txt /tmp/sot_source.txt >/dev/null; then
  echo "  ✅ Container BERISI kode yang IDENTIK dengan source ($(wc -l < /tmp/sot_jalan.txt) file)"
else
  echo "  ⚠️  Container BEDA dari source!"
  diff /tmp/sot_jalan.txt /tmp/sot_source.txt | head -10
fi

# ── CONTOH DOKUMEN untuk UJI (AKAR 16Sep26) ───────────────────────────
# ══ KENAPA DITARUH DI SINI (akar masalah, bukan tambalan) ══════════════
# 16Sep26 uji `_uji_lapis1` & `_uji_catatan_ai` GAGAL karena berkas contoh
# (`_contoh-dokumen/…docx`) TIDAK ADA di container. Akarnya: `jalankan.sh`
# TIDAK PERNAH menyalinnya, jadi SETIAP deploy menghapusnya (container
# dibuat ulang dari image) → uji mati → bug tersembunyi lolos.
# Tambalan = `docker cp` manual tiap kali (sering terlupa).
# Perbaikan permanen = deploy sendiri yang menyalin + MEMERIKSA jumlahnya.
if [ -d "$PROYEK/_contoh-dokumen" ]; then
  N_CONTOH=$(find "$PROYEK/_contoh-dokumen" -name '*.docx' | wc -l)
  if [ "$N_CONTOH" -gt 0 ]; then
    docker exec "$NAMA_CONTAINER" mkdir -p /app/_contoh-dokumen
    docker cp "$PROYEK/_contoh-dokumen/." "$NAMA_CONTAINER:/app/_contoh-dokumen/" >/dev/null 2>&1
    N_ADA=$(docker exec "$NAMA_CONTAINER" sh -c \
      "find /app/_contoh-dokumen -name '*.docx' 2>/dev/null | wc -l")
    if [ "$N_ADA" -eq "$N_CONTOH" ]; then
      echo "  ✅ Contoh dokumen uji tersalin: $N_ADA berkas .docx"
    else
      echo "  ⚠️  Contoh dokumen TIDAK lengkap: $N_ADA dari $N_CONTOH"
      echo "     (uji lapis1/catatan_ai akan gagal — periksa _contoh-dokumen/)"
    fi
  else
    echo "  ⚠️  _contoh-dokumen/ ADA tapi TIDAK berisi .docx → uji akan gagal"
    echo "     (pulihkan dari _arsip/contoh-dokumen/)"
  fi
else
  echo "  ⚠️  _contoh-dokumen/ TIDAK ADA → uji lapis1/catatan_ai akan gagal"
  echo "     (pulihkan: cp -r _arsip/contoh-dokumen/* _contoh-dokumen/)"
fi

# ── WUJUD RESMI IKON LUCIDE untuk GERBANG KEASLIAN (AKAR 06Okt26) ──────
# ══ KENAPA DITARUH DI SINI (akar masalah, bukan tambalan) ══════════════
# 06Okt26 gerbang `_gerbang_ikon_asli.py` GAGAL di produksi dengan
# "62 beda" PALSU. Akarnya: simpanan wujud resmi (`_ikon-asli/*.txt`)
# TIDAK PERNAH disalin oleh `jalankan.sh` ⇒ setiap deploy menghapusnya
# (container dibuat ulang dari image) ⇒ gerbang MEMBACA KOSONG ⇒ semua
# ikon dianggap "tanpa sumber". Tambalan = `docker cp` manual tiap kali
# (persis kesalahan yang sudah terjadi di _contoh-dokumen).
# Perbaikan permanen = deploy sendiri yang menyalin + MEMERIKSA jumlahnya.
if [ -d "$PROYEK/_ikon-asli" ]; then
  N_IKON=$(find "$PROYEK/_ikon-asli" -name '*.txt' | wc -l)
  if [ "$N_IKON" -gt 0 ]; then
    docker exec "$NAMA_CONTAINER" mkdir -p /app/_ikon-asli
    docker cp "$PROYEK/_ikon-asli/." "$NAMA_CONTAINER:/app/_ikon-asli/" >/dev/null 2>&1
    N_ADA=$(docker exec "$NAMA_CONTAINER" sh -c \
      "find /app/_ikon-asli -name '*.txt' 2>/dev/null | wc -l")
    if [ "$N_ADA" -eq "$N_IKON" ]; then
      echo "  ✅ Wujud resmi ikon tersalin: $N_ADA berkas (gerbang keaslian bisa jalan offline)"
    else
      echo "  ⚠️  Wujud ikon TIDAK lengkap: $N_ADA dari $N_IKON"
      echo "     (_gerbang_ikon_asli.py mode offline akan salah lapor — jalankan --online)"
    fi
  else
    echo "  ⚠️  _ikon-asli/ ADA tapi KOSONG → gerbang keaslian salah lapor"
  fi
else
  echo "  ⚠️  _ikon-asli/ TIDAK ADA → gerbang keaslian harus jalan dengan --online"
fi

# ── Verifikasi DB masih terbaca ────────────────────────────────────────
echo
echo "── Verifikasi data (SOT data ada di bind-mount /app/data) ──────"
docker exec "$NAMA_CONTAINER" /usr/local/bin/python -c "
import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
t = [r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")]
n_user = c.execute('SELECT COUNT(*) FROM users').fetchone()[0]
n_file = c.execute('SELECT COUNT(*) FROM files').fetchone()[0]
print(f'  ✅ DB terbaca: {len(t)} tabel | users={n_user} | files={n_file}')
c.close()
"

echo
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ DEPLOY SOT SELESAI"
echo "═══════════════════════════════════════════════════════════════"
echo "  Image jalan  : ${IMAGE_BASE}:${TAG}"
echo "  Titik mundur : ${IMAGE_BASE}:cadangan-pra-sot"
echo "  Backup DB    : ${DIR:-'(dilewati)'}"
echo "  URL          : http://127.0.0.1:${PORT_APP}  (host: $PORT_HOST)"
echo
echo "  CATATAN: mulai sekarang JANGAN pakai 'docker cp app/...' lagi."
echo "           Semua perubahan kode → edit source → bash jalankan.sh"
echo "═══════════════════════════════════════════════════════════════"

# ── GERBANG AKHIR: jaringan & OnlyOffice (exit 1 kalau editor mati) ─────
#  Dipasang 30Sep26 setelah insiden /oo/aset 502 (jaringan hilang saat
#  container dibuat ulang → editor dokumen MATI untuk user asli).
echo
echo "── Gerbang jaringan & OnlyOffice ──────────────────────────────"
JAR=$(docker inspect "$NAMA_CONTAINER" \
      --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}')
echo "  jaringan: $JAR"
if ! echo "$JAR" | grep -q 'eduai-net'; then
  echo "  ❌ eduai-net HILANG → app tidak bisa menjangkau oo-converter (editor MATI)"
  exit 1
fi
DNSOO=$(docker exec "$NAMA_CONTAINER" sh -c 'getent hosts oo-converter 2>/dev/null' || true)
if [ -z "$DNSOO" ]; then
  echo "  ❌ nama 'oo-converter' TIDAK teratasi dari dalam app → /oo/aset akan 502"
  exit 1
fi
KODE_OO=$(docker exec "$NAMA_CONTAINER" sh -c \
  'curl -s -o /dev/null -w "%{http_code}" -m 10 http://localhost:8000/oo/aset/web-apps/apps/api/documents/api.js' 2>/dev/null || echo 000)
if [ "$KODE_OO" != "200" ]; then
  echo "  ❌ /oo/aset = $KODE_OO (HARUS 200) → editor OnlyOffice MATI"
  echo "     Obat: bash scripts/jalankan_oo.sh   atau   bash scripts/perbaiki_oo.sh"
  exit 1
fi
echo "  ✅ oo-converter terjangkau · /oo/aset = 200 (editor hidup)"

# ── GERBANG EDITOR: kunci secure_link (akar -4 "Unduhan gagal") ─────────
bash scripts/periksa_editor.sh 2>&1 | grep -E '✓|✗|LULUS|GAGAL' || true
