#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════
#  GERBANG UJI E2E EDUAI — jalankan SEMUA uji sekaligus, satu perintah.
#
#  KENAPA ADA: skrip uji HILANG dari container setiap deploy (docker cp
#  hanya sementara). Sebelumnya tiap uji harus disalin & dijalankan manual
#  → mudah terlupa → regresi lolos. Gerbang ini yang menutup celah itu.
#
#  ⚠️ UJI INGATAN DOKUMEN WAJIB — bug 17Sep26 (`pengali`/list-vs-str)
#     SENYAP: revisi "sukses" tapi section_state & revisi_history KOSONG.
#     Hanya uji ini yang bisa menangkapnya.
#
#  PAKAI:
#     bash scripts/gerbang_uji.sh              # uji CEPAT (N/O/P/Q dilewati)
#     bash scripts/gerbang_uji.sh berkas.docx  # dokumen tertentu
#     E2E_BERAT=1 bash scripts/gerbang_uji.sh  # + N/O/P/Q (potong kuota, lambat)
#
#  Keluar 0 = SEMUA LULUS (aman deploy). Bukan 0 = ADA GAGAL.
#
#  ⚠️ KENAPA N/O/P/Q DIPISAH (akar 5 GAGAL PALSU 17Sep26): uji itu memotong
#     kuota & memanggil AI beruntun → kuota habis (402) + rate limit (429)
#     → GAGAL PALSU, bukan bug app. Gerbang harian WAJIB cepat & hijau.
# ══════════════════════════════════════════════════════════════════════════
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP=eduai-app
BOT=hermes
BERKAS=""
#  Argumen pertama = berkas, KECUALI berisi '=' (itu variabel env).
if [ "${1:-}" != "" ] && [[ "${1}" != *=* ]]; then BERKAS="$1"; fi
export E2E_BERAT="${E2E_BERAT:-0}"
export E2E_JEDA="${E2E_JEDA:-2}"
LULUS_TOTAL=0
GAGAL_TOTAL=0
GAGAL_NAMA=()

biru()  { printf '\n\033[1;36m%s\033[0m\n' "$*"; }
hijau() { printf '\033[1;32m%s\033[0m\n' "$*"; }
merah() { printf '\033[1;31m%s\033[0m\n' "$*"; }

catat() {  # catat <nama-uji> <exit-code>
  if [ "$2" -eq 0 ]; then
    LULUS_TOTAL=$((LULUS_TOTAL + 1))
  else
    GAGAL_TOTAL=$((GAGAL_TOTAL + 1))
    GAGAL_NAMA+=("$1")
  fi
}

# ── 0. PRASYARAT: container hidup ─────────────────────────────────────────
biru "══ 0. PRASYARAT ══"
for c in "$APP" "$BOT"; do
  if docker ps --format '{{.Names}}' | grep -qx "$c"; then
    hijau "  ✅ container $c hidup"
  else
    merah "  ❌ container $c TIDAK hidup → uji dibatalkan"
    exit 2
  fi
done
#  ⚠️ JANGAN `curl http://127.0.0.1:8100/health` — Wulan/hermes jalan DI DALAM
#     container, jadi 127.0.0.1 = loopback container ini, BUKAN VPS. Port 8100
#     hanya ada di sisi host. Hasilnya selalu HTTP 000 (menyesatkan!).
#     Cek dari DALAM container eduai-app lewat docker exec.
HEALTH=$(docker exec "$APP" curl -s -o /dev/null -w '%{http_code}' \
         http://127.0.0.1:8000/health 2>/dev/null || echo '?')
if [ "$HEALTH" = "200" ]; then
  hijau "  ✅ /health (dari dalam container): $HEALTH"
else
  merah "  ❌ /health: $HEALTH → app TIDAK sehat, uji dibatalkan"
  exit 2
fi

IMAGE=$(docker inspect "$APP" --format '{{.Config.Image}}' 2>/dev/null || echo '?')
echo "  Image: $IMAGE"

# ── 1. SALIN SKRIP UJI (hilang tiap deploy) ───────────────────────────────
biru "══ 1. SALIN SKRIP UJI KE CONTAINER ══"
docker cp "$DIR/_uji_publik_komentar.py" "$BOT:/tmp/"   >/dev/null 2>&1 && hijau "  ✅ ke $BOT" || merah "  ⚠️  gagal salin ke $BOT"
docker cp "$DIR/_uji_ingatan.py"         "$APP:/app/"   >/dev/null 2>&1 && hijau "  ✅ ke $APP" || merah "  ⚠️  gagal salin ke $APP"
#  C10 (25Sep26): uji `_uji_c10_versi_kosong.py` memanggil skrip ini untuk
#  MEMOTONG & MENJALANKAN pagar di ai.py — wajib ikut tersalin.
docker cp "$DIR/_periksa_pagar_c10.py"   "$APP:/app/"   >/dev/null 2>&1 || true

# ── 2. UJI FUNGSI (regresi satuan, cepat, Rp 0) ───────────────────────────
biru "══ 2. UJI FUNGSI (regresi satuan, tanpa AI) ══"
for f in _uji_lapis1.py _uji_fase5_hipo.py _uji_fase5_jalur.py \
         _uji_pembersih.py _uji_catatan_ai.py _uji_etika.py \
         _uji_citation_validator.py _uji_c4_bab.py _uji_c4_bab_http.py \
         _uji_c5_label.py _uji_c9_kosong.py _uji_c6_sabar.py \
         _uji_c10_versi_kosong.py; do
  if [ ! -f "$DIR/$f" ]; then
    printf '  ⚠️  %-32s (berkas tidak ada — dilewati)\n' "$f"
    continue
  fi
  docker cp "$DIR/$f" "$APP:/app/" >/dev/null 2>&1
  out=$(docker exec -w /app "$APP" python3 "$f" 2>&1)
  rc=$?
  #  Ringkasan BERBEDA tiap skrip: "17 LULUS / 0 GAGAL", "17 OK / 0 GAGAL",
  #  "26 LULUS   GAGAL: 0", "LULUS". Ambil baris ringkasan terakhir apa pun.
  #  ⚠️  SATU-SATUNYA penentu LULUS/GAGAL = EXIT CODE. Jangan menebak dari
  #      teks — pola grep "GAGAL" cocok juga di baris "26 LULUS  GAGAL: 0"
  #      → dulu menandai GAGAL padahal lulus (over-koreksi 17Sep26).
  ringkas=$(printf '%s' "$out" \
    | grep -oE '[0-9]+ *(LULUS|OK)[^0-9]*([0-9]+ *(GAGAL|GALAT):? *[0-9]+)?' \
    | tail -1)
  if [ $rc -eq 0 ]; then
    printf '  ✅ %-32s %s\n' "$f" "${ringkas:-LULUS}"
  else
    printf '  ❌ %-32s %s  (exit %d)\n' "$f" "${ringkas:-GAGAL}" "$rc"
    printf '%s\n' "$out" | tail -15
  fi
  catat "$f" "$rc"
done

# ── 2b. UJI TAHAP 2 — KOLABORASI PEMBIMBING (WAJIB, ACC Bos 24Sep26) ──────
#  ⚠️ KENAPA WAJIB: kode Tahap 2 (tautan pembimbing, lampiran, log 3 lapis,
#     halaman tinjau) sebelum ini HANYA diuji manual → kalau ada yang
#     menyentuh app/pembimbing.py atau templates, rusaknya tidak ketahuan.
#     Semua uji di bawah Rp 0 (tanpa AI) dan cepat.
biru "══ 2b. UJI TAHAP 2 — KOLABORASI PEMBIMBING ══"
#  ⚠️ URUTAN PENTING (akar 2 GAGAL PALSU 24Sep26): `_uji_kelompok_bab.py`
#     dan `_uji_presisi_dropdown_http.py` memakai `file_id` yang SAMA
#     (satu berkas nyata). Siapa jalan terakhir, isi naskahnya yang menang
#     → uji lain jadi GAGAL PALSU. Karena itu SIAPKAN data 2.5 dulu, lalu
#     jalankan `_uji_kelompok_bab.py` TEPAT SESUDAHNYA.
if [ -f "$DIR/_sketsa/siapkan_uji_25.py" ]; then
  docker exec "$APP" python3 -c "
import sys; sys.path.insert(0,'/app')
from app.models import SessionLocal, VersiDokumen, init_db
init_db(); db=SessionLocal()
db.query(VersiDokumen).filter(VersiDokumen.sumber=='uji').delete()
db.commit(); db.close()" >/dev/null 2>&1
  docker cp "$DIR/_sketsa/siapkan_uji_25.py" "$APP:/app/_siap25.py" >/dev/null 2>&1
  docker exec -w /app "$APP" python3 /app/_siap25.py >/dev/null 2>&1 \
    && hijau "  ✅ data uji 2.5 disiapkan ulang" \
    || merah "  ⚠️  gagal siapkan data uji 2.5"
fi
for f in _uji_pembimbing.py _uji_pembimbing_http.py _uji_bagikan.py \
         _uji_lampiran.py _uji_log_revisi.py _uji_tahan_gempa_tinjau.py \
         _uji_kelompok_bab.py _uji_presisi_dropdown_http.py \
         _uji_luncur_naskah.py _uji_sorotan.py; do
  if [ ! -f "$DIR/$f" ]; then
    printf '  ⚠️  %-32s (berkas tidak ada — dilewati)\n' "$f"
    continue
  fi
  docker cp "$DIR/$f" "$APP:/app/" >/dev/null 2>&1
  out=$(docker exec -w /app "$APP" python3 "$f" 2>&1)
  rc=$?
  ringkas=$(printf '%s' "$out" \
    | grep -oE '[0-9]+ *(LULUS|OK)[^0-9]*([0-9]+ *(GAGAL|GALAT):? *[0-9]+)?' \
    | tail -1)
  if [ $rc -eq 0 ]; then
    printf '  ✅ %-32s %s\n' "$f" "${ringkas:-LULUS}"
  else
    printf '  ❌ %-32s %s  (exit %d)\n' "$f" "${ringkas:-GAGAL}" "$rc"
    printf '%s\n' "$out" | grep -E '❌|GAGAL' | head -8
  fi
  catat "$f" "$rc"
done

# ── 3. UJI INGATAN DOKUMEN (WAJIB — penangkap bug senyap) ─────────────────
biru "══ 3. UJI INGATAN DOKUMEN (penangkap bug SENYAP 17Sep26) ══"
out=$(docker exec -w /app "$APP" python3 _uji_ingatan.py 2>&1)
rc=$?
printf '%s\n' "$out" | grep -E 'HASIL|❌' || true
catat "_uji_ingatan" "$rc"

# ── 4. UJI E2E JALUR PUBLIK (dengan AI — potong kuota, tetapi direset) ────
biru "══ 4. UJI E2E JALUR MAHASISWA (domain publik + AI nyata) ══"
echo "  (potong kuota user uji — direset setelah selesai)"
if [ "$E2E_BERAT" = "1" ]; then
  hijau "  🔥 E2E_BERAT=1 → skenario N/O/P/Q IKUT dijalankan (lambat, potong kuota)"
else
  echo "  (N/O/P/Q DILEWATI — pakai E2E_BERAT=1 untuk ikut)"
fi
#  🔴 AKAR DIPERBAIKI 05Okt26 (D1) — reset SEBELUM uji. Sama seperti reset
#  di akhir (§5): 402 = SALDO `saldo_token`, bukan `pemakaian_ai`. Tanpa
#  baris saldo di bawah, D1–D6 SELALU kena 402 → GAGAL PALSU tiap hari.
docker exec "$APP" python3 -c "
import sqlite3
c=sqlite3.connect('/app/data/eduai.db')
c.execute('UPDATE pemakaian_ai SET jumlah_revisi=0 WHERE user_id=6')
c.execute(\"DELETE FROM saldo_token WHERE user_id IN (6,7) AND catatan LIKE 'saldo uji gerbang harian%'\")
for uid in (6,7):
    ada = c.execute('SELECT sisa FROM saldo_token WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
    sisa = (ada[0] if ada else 0) or 0
    if sisa < 20:
        c.execute(\"INSERT INTO saldo_token(user_id,jumlah,sisa,sumber,catatan,order_id,dibuat) \"
                  \"VALUES(?,?,?,'uji','saldo uji gerbang harian',?,datetime('now'))\",
                  (uid, 20-sisa, 20, ''))
c.commit()
for uid in (6,7):
    r=c.execute('SELECT sisa FROM saldo_token WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
    print(f'  user {uid} saldo -> {r[0] if r else None}')
" 2>/dev/null
if [ -n "$BERKAS" ]; then
  out=$(docker exec -e E2E_BERAT="$E2E_BERAT" -e E2E_JEDA="$E2E_JEDA" \
        -e E2E_SAYA_SETUJU=1 \
        "$BOT" python3 /tmp/_uji_publik_komentar.py "$BERKAS" 2>&1)
else
  # 🚨 AKAR GAGAL SENYAP (05Okt26): uji ini MEMINTA persetujuan
  #    (E2E_SAYA_SETUJU) karena memakai kuota + menulis DB nyata. Tanpa
  #    variabel itu, uji hanya mencetak penolakan lalu keluar — gerbang
  #    membacanya sebagai GAGAL, padahal tak satu pun asersi dijalankan.
  #    Gerbang sudah mereset kuota user uji 2 baris di atas, jadi
  #    persetujuan memang tempatnya di sini.
  out=$(docker exec -e E2E_BERAT="$E2E_BERAT" -e E2E_JEDA="$E2E_JEDA" \
        -e E2E_SAYA_SETUJU=1 \
        "$BOT" python3 /tmp/_uji_publik_komentar.py 2>&1)
fi
rc=$?
printf '%s\n' "$out" | grep -E '^HASIL|❌|KODE_PROSES|FILE_ID' || true
catat "_uji_publik_komentar" "$rc"

# ── 4b. UJI NOTIFIKASI (WAJIB — gerbang gaya bahasa, ACC Bos 17Sep26) ────
#  ⚠️ KENAPA WAJIB: aturan Bos "notifikasi harus hangat, jangan menakutkan"
#     + "sebut pelaku sebagai EduAi" mudah rusak diam-diam begitu ada yang
#     menambah kalimat baru. Uji ini yang menjaga. Cepat (tanpa AI).
biru "══ 4b. UJI KATA NOTIFIKASI (gaya bahasa + sebutan EduAi) ══"
for f in uji_notifikasi_kata uji_lonceng_gagal uji_pemicu_notifikasi uji_pembatalan_kuota uji_riwayat_per_komentar; do
  docker cp "$DIR/scripts/$f.py" "$APP:/app/" >/dev/null 2>&1
  out=$(docker exec -w /app "$APP" python3 "/app/$f.py" 2>&1)
  rc=$?
  ringkas=$(printf '%s\n' "$out" | grep -oE '[0-9]+ LULUS / [0-9]+ GAGAL' | tail -1)
  if [ $rc -eq 0 ]; then
    printf '  ✅ %-32s %s\n' "$f" "${ringkas:-LULUS}"
  else
    printf '  ❌ %-32s %s  (exit %d)\n' "$f" "${ringkas:-GAGAL}" "$rc"
    printf '%s\n' "$out" | grep -E '❌' | head -8
  fi
  catat "$f" "$rc"
done

# ── 5. UJI INGATAN ULANG (setelah E2E — WAJIB terisi) ─────────────────────
biru "══ 5. INGATAN SETELAH E2E (bukti akhir) ══"
KODE=$(printf '%s' "$out" | grep -oE 'KODE_PROSES=[A-Za-z0-9_-]+' | head -1 | cut -d= -f2)
if [ -n "$KODE" ]; then
  out2=$(docker exec -w /app "$APP" python3 _uji_ingatan.py --kode "$KODE" 2>&1)
  rc2=$?
  printf '%s\n' "$out2" | grep -E 'I2a|I3a|HASIL|❌' || true
  catat "_uji_ingatan_after_e2e" "$rc2"
else
  merah "  ⚠️  kode proses tidak terbaca → uji ingatan lanjutan dilewati"
fi

# ── RESET KUOTA USER UJI (jangan tinggalkan jatah habis) ──────────────────
#  🔴 AKAR DIPERBAIKI 05Okt26 (D1) — gerbang GAGAL PALSU 5 asersi beruntun.
#  GEJALA: `_uji_publik_komentar` selalu "15 LULUS / 5 GAGAL" dengan
#    D1 = HTTP 402 `kode=KUOTA_HABIS` — angkanya TIDAK BERUBAH walau kode
#    aplikasi diganti, dan perubahan itu tidak menyentuh kuota sama sekali.
#  AKAR (terukur dari DB): baris lama hanya reset `pemakaian_ai`, PADAHAL
#    402 = SALDO `saldo_token` (sudah terbukti: 402 revisi = saldo_token,
#    BUKAN pemakaian_ai). Saldo user uji 6 = 0 → SETIAP kali kena 402.
#  KENAPA BERBAHAYA: gerbang merah palsu = orang berhenti percaya gerbang,
#    dan kerusakan NYATA bisa tersembunyi di dalamnya.
#  AKAR KEDUA: saldo_token bentuknya BUKU BESAR (ledger, 'pakai' menulis
#    baris sisa=0). Menulis ulang baris lama = MEMALSUKAN sejarah pemakaian
#    user. Karena itu baris `sumber='pakai'` TIDAK PERNAH disentuh/timpa —
#    pengembalian dana uji dicatat sebagai baris BARU yang jujur.
docker exec "$APP" python3 -c "
import sqlite3
c=sqlite3.connect('/app/data/eduai.db')
# (1) kuota bulanan — kolom ini memang dipakai uji lain
c.execute('UPDATE pemakaian_ai SET jumlah_revisi=0 WHERE user_id=6')
# (2) AKAR: SALDO token uji — 402 selalu dari sini.
#     ⚠️ Pola baris MENGIKUTI yang SUDAH ADA di DB (sumber='uji', order_id='')
#        — bukan bikin pola baru. `jumlah` = selisih menuju 20 supaya sisa
#        akhir PERSIS 20 (pola akuntansi yang sama dipakai baris 'uji' lama).
c.execute(\"DELETE FROM saldo_token WHERE user_id IN (6,7) AND catatan LIKE 'saldo uji gerbang harian%'\")
for uid in (6,7):
    ada = c.execute('SELECT sisa FROM saldo_token WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
    sisa = (ada[0] if ada else 0) or 0
    if sisa < 20:
        c.execute(\"INSERT INTO saldo_token(user_id,jumlah,sisa,sumber,catatan,order_id,dibuat) \"
                  \"VALUES(?,?,?,'uji','saldo uji gerbang harian',?,datetime('now'))\",
                  (uid, 20-sisa, 20, ''))
c.commit()
for uid in (6,7):
    r=c.execute('SELECT sisa FROM saldo_token WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
    print(f'  user {uid} saldo -> {r[0] if r else None}')
" 2>/dev/null \
  && hijau "  ✅ kuota + SALDO user uji direset (siap uji berikutnya)"

# ── 6. SOT PERCABANGAN (penangkap SOT basi — perintah Bos 24Sep26) ────────
#  KENAPA: MASTER_PLAN §7 pernah BASI 11 hari tanpa ketahuan (masih "13 Sep"
#  padahal sudah 24 Sep, dan banyak barisnya sudah salah). Penangkap ini
#  memastikan peta percabangan tetap SEGAR & setiap cabang tetap tercatat.
biru "══ 6. SOT PERCABANGAN ══"
if [ -f "$DIR/scripts/periksa_percabangan.sh" ]; then
  out3=$(bash "$DIR/scripts/periksa_percabangan.sh" 2>&1)
  rc3=$?
  printf '%s\n' "$out3" | grep -E '❌|✅ SOT|BASI' | head -10
  catat "periksa_percabangan" "$rc3"
else
  merah "  ⚠️  scripts/periksa_percabangan.sh tidak ada — SOT tidak terjaga"
  catat "periksa_percabangan" 1
fi

# ── 7. PAGAR MUTU JALUR PETA (14 Okt 2026 — hemat Jev) ────────────────────
#  KENAPA: naskah RUSAK (pecah per-huruf, mis. PDF) pernah membakar ~40
#  panggilan Jev tanpa hasil rapi. Pagar ini melewati surveyor Jev untuk
#  naskah rusak (jalur fallback, Rp 0) — TAPI hanya untuk 'rusak_konversi';
#  naskah sehat WAJIB tetap jalur Jev. Gerbang ini menjaga keduanya.
biru "══ 7. PAGAR MUTU JALUR PETA (hemat Jev) ══"
if [ -f "$DIR/app/_gerbang_pagar_mutu_peta.py" ]; then
  docker cp "$DIR/app/_gerbang_pagar_mutu_peta.py" "$APP:/app/app/" >/dev/null 2>&1
  out4=$(docker exec -w /app "$APP" python3 app/_gerbang_pagar_mutu_peta.py 2>&1)
  rc4=$?
  printf '%s\n' "$out4" | grep -E 'LULUS [0-9]+|GAGAL:|X   ' | tail -6
  catat "pagar_mutu_peta" "$rc4"
else
  merah "  ⚠️  app/_gerbang_pagar_mutu_peta.py tidak ada — pagar mutu tidak terjaga"
  catat "pagar_mutu_peta" 1
fi

# ── 7. PAGAR MUTU JALUR PETA (14 Okt 2026 — hemat Jev) ───────────────────
#  KENAPA: naskah RUSAK (pecah per-huruf, mis. PDF) pernah membakar ~40
#  panggilan Jev tanpa hasil rapi. Pagar ini melewati surveyor Jev untuk
#  naskah rusak (jalur fallback, Rp 0) — TAPI hanya untuk 'rusak_konversi';
#  naskah sehat WAJIB tetap jalur Jev. Gerbang ini menjaga keduanya.
biru "══ 7. PAGAR MUTU JALUR PETA (hemat Jev) ══"
if [ -f "$DIR/app/_gerbang_pagar_mutu_peta.py" ]; then
  docker cp "$DIR/app/_gerbang_pagar_mutu_peta.py" "$APP:/app/app/" >/dev/null 2>&1
  out4=$(docker exec -w /app "$APP" python3 app/_gerbang_pagar_mutu_peta.py 2>&1)
  rc4=$?
  printf '%s\n' "$out4" | grep -E 'LULUS [0-9]+|GAGAL:|X   ' | tail -6
  catat "pagar_mutu_peta" "$rc4"
else
  merah "  ⚠️  app/_gerbang_pagar_mutu_peta.py tidak ada — pagar mutu tidak terjaga"
  catat "pagar_mutu_peta" 1
fi

# ── 8. RAPI_BAB (14 Okt 2026 — catatan pembimbing → peta Jev) ───────────
#  KENAPA: pembimbing tulis bab 3 cara ('BAB III', 'BAB 3', 'bab iii')
#  tapi peta Jev pakai angka ('3'). Ini bikin catatan pembimbing tidak
#  nyambung ke revisi AI mahasiswa. Fungsi rapi_bab() di pembimbing.py +
#  asisten.py menyamakan jadi satu bentuk.
biru "══ 8. RAPI BAB PEMBIMBING (sinkron catatan → peta Jev) ══"
if [ -f "$DIR/app/_gerbang_rapi_bab.py" ]; then
  docker cp "$DIR/app/_gerbang_rapi_bab.py" "$APP:/app/app/" >/dev/null 2>&1
  out5=$(docker exec -w /app "$APP" python3 app/_gerbang_rapi_bab.py 2>&1)
  rc5=$?
  printf '%s\n' "$out5" | grep -E 'LULUS [0-9]+|GAGAL:|X   ' | tail -6
  catat "rapi_bab" "$rc5"
else
  merah "  ⚠️  app/_gerbang_rapi_bab.py tidak ada — catatan pembimbing tak nyambung ke peta"
  catat "rapi_bab" 1
fi

# ── 9. BATAS BAB (15 Okt 2026 — bug disertasi 7 bab) ────────────────────
#  KENAPA: batas bab dulu 5 (`_angka_romawi`) & 9 (`_nomor_bab_dari_section`).
#  Akibat NYATA (terukur): disertasi 7 bab → label bab 6 jadi 'BAB 6'
#  (naskah pakai 'BAB VI') → Mode Belajar bab 6-8 MATI. Naskah 10 bab →
#  'BAB X' DITOLAK SENYAP. Bukti: peta Jev fid=112 punya 'BAB VI'.
biru "══ 9. BATAS BAB (disertasi 7 bab) ══"
if [ -f "$DIR/app/_gerbang_batas_bab.py" ]; then
  docker cp "$DIR/app/_gerbang_batas_bab.py" "$APP:/app/app/" >/dev/null 2>&1
  out6=$(docker exec -w /app "$APP" python3 app/_gerbang_batas_bab.py 2>&1)
  rc6=$?
  printf '%s\n' "$out6" | grep -E 'LULUS [0-9]+|GAGAL:|X   ' | tail -6
  catat "batas_bab" "$rc6"
else
  merah "  ⚠️  app/_gerbang_batas_bab.py tidak ada — batas bab tak terjaga"
  catat "batas_bab" 1
fi

# ── 10. JEV BUKU UMUM + AMBANG PARAGRAF (20 Okt 2026) ──────────────────
#  KENAPA: (a) naskah buku bukan naskah akademik — Jev akademik buta pada
#  judul yang menempel dengan isi; (b) ambang `merge_short_paragraphs`
#  ditulis MATI 50 kata padahal tone buku anak 25-40 ⇒ seluruh bab menjadi
#  SATU baris 8.251 karakter. Dua gerbang ini menjaga keduanya.
biru "══ 10. JEV BUKU UMUM + AMBANG PARAGRAF ══"
for g in gerbang_jev_buku gerbang_ambang_paragraf gerbang_verifikasi_sitasi gerbang_tabel_buku uji_parser_tabel gerbang_keluhan_20okt uji_gigi_gerbang_keluhan gerbang_placeholder_brief gerbang_penanda_jadi_gambar uji_gigi_penanda; do
  if [ -f "$DIR/$g.py" ]; then
    docker cp "$DIR/$g.py" "$APP:/app/" >/dev/null 2>&1
    outX=$(docker exec -w /app "$APP" python3 "$g.py" 2>&1)
    rcX=$?
    printf '%s\n' "$outX" | grep -E '"lulus"|GAGAL ' | tail -4
    catat "$g" "$rcX"
  else
    merah "  ⚠️  $g.py tidak ada — bentuk naskah buku tak terjaga"
    catat "$g" 1
  fi
done

# ── RINGKASAN ─────────────────────────────────────────────────────────────
echo
echo "════════════════════════════════════════════════════════════════"
echo "  GERBANG UJI: $LULUS_TOTAL grup LULUS / $GAGAL_TOTAL grup GAGAL"
if [ "$GAGAL_TOTAL" -gt 0 ]; then
  merah "  ❌ GAGAL: ${GAGAL_NAMA[*]}"
  echo "  ⚠️  JANGAN deploy sebelum semua LULUS."
else
  hijau "  ✅ SEMUA LULUS — aman deploy."
fi
echo "  Image saat ini: $IMAGE"
echo "════════════════════════════════════════════════════════════════"
exit "$GAGAL_TOTAL"
