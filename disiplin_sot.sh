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
# ═══════════════════════════════════════════════════════════════════════
#  disiplin_sot.sh — PENJAGA SOT
# ═══════════════════════════════════════════════════════════════════════
#  Cek apakah kode di container produksi BAKU (= hasil build dari source).
#  Kalau ada file kode yang "nyelip" (hanya ada di container), berarti
#  ada yang pakai `docker cp` — PELANGGARAN SOT.
#
#  CARA PAKAI:  bash disiplin_sot.sh
#  KAPAN:       setelah deploy, sebelum lapor, atau kapan saja curiga
# ═══════════════════════════════════════════════════════════════════════
set -uo pipefail
cd /opt/data/services/eduai-publishing
CT="eduai-app"

echo "═══════════════════════════════════════════════════════════"
echo "  AUDIT DISIPLIN SOT — $(date '+%d %b %Y %H:%M')"
echo "═══════════════════════════════════════════════════════════"

echo
echo "── 1. Container jalan dari image apa ──"
docker inspect "$CT" --format '  {{.Config.Image}}  ({{.State.Status}})'

echo
echo "── 2. File KODE yang nyelip di container (harus KOSONG) ──"
NYELIP=$(docker diff "$CT" | grep -E "^[ACD] /app/(app|prompts)" | grep -vE "/__pycache__" || true)
if [ -z "$NYELIP" ]; then
  echo "  ✅ BERSIH — tidak ada kode di luar image"
else
  echo "  ❌ DITEMUKAN KODE NYELIP (pelanggaran SOT):"
  echo "$NYELIP" | sed 's/^/     /'
  echo
  echo "  → Artinya ada yang pakai 'docker cp'. Perbaiki:"
  echo "     bash jalankan.sh"
fi

echo
echo "── 3. Ringkasan docker diff ──"
echo "  ditambah : $(docker diff "$CT" | grep -c '^A')"
echo "  diubah   : $(docker diff "$CT" | grep -c '^C')"
echo "  dihapus  : $(docker diff "$CT" | grep -c '^D')"
echo "  (sehat = ~2 tambah + 1 ubah, hanya data/uploads)"

echo
echo "── 4. Kode container == source? ──"
docker exec "$CT" sh -c "cd /app && find app -type f -name '*.py' -exec md5sum {} \;" 2>/dev/null | sort -k2 > /tmp/_sot_ct.txt
find app -type f -name '*.py' -exec md5sum {} \; | sort -k2 > /tmp/_sot_src.txt
if diff -q /tmp/_sot_ct.txt /tmp/_sot_src.txt >/dev/null 2>&1; then
  echo "  ✅ IDENTIK — $(wc -l < /tmp/_sot_src.txt) file .py cocok"
else
  echo "  ❌ BEDA:"
  diff /tmp/_sot_ct.txt /tmp/_sot_src.txt | head -15 | sed 's/^/     /'
fi

echo
echo "── 5. Skrip lama yang masih pakai 'docker cp' KODE ──"
SISA=$(grep -rln "eduai-app:/app/app\|eduai-app:/app/prompts" \
        --include="*.sh" --include="*.py" . 2>/dev/null \
        | grep -v "^./_arsip" | grep -v "jalankan.sh" \
        | grep -v "disiplin_sot.sh" | grep -v "_cari_docker_cp" \
        | grep -v "_klasifikasi" | grep -v "_pasang_penjaga" || true)
if [ -z "$SISA" ]; then
  echo "  ✅ TIDAK ADA — semua sudah bersih"
else
  echo "  ❌ MASIH ADA:"
  echo "$SISA" | sed 's/^/     /'
fi

echo
echo "── 6. STANDAR 24Sep26: kode nyelip → WAJIB sudah restart ──"
#  KENAPA DIPERIKSA (terukur 24Sep26): `docker cp` hanya menukar berkas di
#  disk; server yang sedang jalan TIDAK membacanya ulang karena container
#  dijalankan TANPA `--reload`. Kalau ada kode nyelip TAPI container belum
#  pernah restart sesudahnya, maka yang benar-benar JALAN masih kode LAMA —
#  uji apa pun jadi tidak sah.
if [ -z "$NYELIP" ]; then
  echo "  ✅ tidak ada kode nyelip → tidak ada risiko kode lama"
else
  MULAI=$(docker inspect "$CT" --format '{{.State.StartedAt}}' 2>/dev/null)
  echo "  ⚠️  ADA kode nyelip di container."
  echo "      Container mulai terakhir : $MULAI"
  echo "      → Kalau kode itu disalin SESUDAH waktu itu, server MASIH"
  echo "        memakai kode lama. Jalankan:"
  echo "           bash scripts/salin_restart.sh $CT --periksa"
  echo "        lalu salin ulang lewat skrip (yang otomatis restart)."
  echo "      → Untuk TAYANG produksi tetap: bash jalankan.sh"
fi

echo
echo "── 7. Container jalan TANPA --reload? (sebab akar) ──"
CMD_JSON=$(docker inspect "$CT" --format '{{json .Config.Cmd}}' 2>/dev/null)
echo "  $CMD_JSON"
if printf '%s' "$CMD_JSON" | grep -q -- '--reload'; then
  echo "  ℹ️  ada --reload → perubahan berkas otomatis terbaca"
else
  echo "  ℹ️  TANPA --reload → kode dimuat SEKALI saat start."
  echo "      ⇒ setiap 'docker cp' KODE **WAJIB** diikuti 'docker restart'."
  echo "      ⇒ pakai: bash scripts/salin_restart.sh $CT <berkas>"
fi

echo
echo "═══════════════════════════════════════════════════════════"
