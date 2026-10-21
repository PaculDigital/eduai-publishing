#!/usr/bin/env bash
# TUKAR state.db (Hermes) — AMAN & BERTAHAP
#
# KENAPA SKRIP INI ADA:
#   state.db menahan 2,9 GB. Sudah dirapikan jadi ~2 GB (indeks dibangun ulang,
#   NOL pesan hilang). Skrip ini memasang hasil rapikan dengan hati-hati.
#
# ⚠️ JEBAKAN YANG SUDAH KENA (15 Okt 2026):
#   /tmp (overlay) dan /opt/data (/dev/sda2) = PARTISI BEDA.
#   `mv` antar partisi = SALIN + HAPUS ⇒ butuh ruang 2× di tujuan.
#   Dulu disk penuh di tengah jalan ⇒ file rusak ("database disk image is
#   malformed"). Karena itu skrip ini: (1) cek ruang DULU, (2) `cp` bukan `mv`,
#   (3) verifikasi integritas SEBELUM menimpa, (4) sisakan .lama sebagai mundur.
#
# CARA PAKAI:
#   bash scripts/tukar_state.sh --periksa    # cek saja, tidak mengubah apa pun
#   bash scripts/tukar_state.sh              # jalankan penukaran
#
# DILARANG dijalankan saat Bos sedang bekerja — percakapan akan terputus.

set -u
BARU="${BARU:-/tmp/state-kerja.db}"
LAMA="/opt/data/state.db"
MUNDUR="/opt/data/_siap-tukar-state/state-lama.db"

merah() { printf '\033[31m%s\033[0m\n' "$1"; }
hijau() { printf '\033[32m%s\033[0m\n' "$1"; }
biru()  { printf '\033[36m%s\033[0m\n' "$1"; }

MODE="${1:-jalan}"

biru "═══ 1. CEK BERKAS BARU ═══"
if [ ! -f "$BARU" ]; then merah "  ❌ $BARU tidak ada"; exit 1; fi
UKURAN_BARU=$(stat -c%s "$BARU")
printf '  %s : %.1f MB\n' "$BARU" "$(python3 -c "print(f'{$UKURAN_BARU/1048576:.1f}')")"

biru "═══ 2. CEK INTEGRITAS & ISI (wajib lolos) ═══"
python3 - "$BARU" <<'PY'
import sqlite3, sys
p = sys.argv[1]
c = sqlite3.connect('file:%s?mode=ro' % p, uri=True)
ic = c.execute('pragma quick_check').fetchone()[0]
n  = c.execute('select count(*) from messages').fetchone()[0]
s  = c.execute('select count(*) from sessions').fetchone()[0]
t  = c.execute("select count(*) from messages_fts_trigram").fetchone()[0]
print('  integrity      :', ic)
print('  pesan          :', n)
print('  sesi           :', s)
print('  trigram (cari) :', t)
c.close()
if ic != 'ok':
    print('  ❌ INTEGRITAS RUSAK — JANGAN dipakai'); sys.exit(1)
if n < 1000:
    print('  ❌ pesan terlalu sedikit — mencurigakan'); sys.exit(1)
if s < 10:
    print('  ❌ sesi terlalu sedikit — mencurigakan'); sys.exit(1)
if t != n:
    print('  ⚠️  trigram (%d) != pesan (%d) — indeks cari belum lengkap' % (t, n))
    sys.exit(2)
print('  ✅ lolos')
PY
RC=$?
if [ "$RC" = "1" ]; then merah "  ❌ verifikasi GAGAL — dibatalkan"; exit 1; fi
if [ "$RC" = "2" ]; then merah "  ⚠️  indeks cari belum lengkap — tunggu selesai dulu"; exit 1; fi

biru "═══ 3. CEK RUANG DISK ═══"
mkdir -p "$(dirname "$MUNDUR")"
BEBAS_KB=$(df -Pk /opt/data | awk 'NR==2{print $4}')          # KB
BUTUH_KB=$(( (UKURAN_BARU + $(stat -c%s "$LAMA" 2>/dev/null || echo 0)) / 1024 ))
printf '  bebas di /opt/data : %s GB\n' "$(awk "BEGIN{printf \"%.2f\", $BEBAS_KB/1048576}")"
printf '  perlu (baru+lama)  : %s GB\n' "$(awk "BEGIN{printf \"%.2f\", $BUTUH_KB/1048576}")"
if [ "$BEBAS_KB" -lt "$BUTUH_KB" ]; then
  merah "  ❌ ruang TIDAK cukup — mundurkan dulu (hapus berkas lama)"
  exit 1
fi
hijau "  ✅ ruang cukup"

if [ "$MODE" = "--periksa" ]; then
  hijau "── MODE PERIKSA: semua siap. Tidak ada yang diubah. ──"
  exit 0
fi

biru "═══ 4. SIMPAN YANG LAMA (titik mundur) ═══"
if [ ! -f "$MUNDUR" ]; then
  cp "$LAMA" "$MUNDUR" || { merah "  ❌ gagal menyalin mundur"; exit 1; }
  hijau "  ✅ tersimpan: $MUNDUR"
else
  printf '  (sudah ada: %s)\n' "$MUNDUR"
fi

biru "═══ 5. PASANG YANG BARU ═══"
cp "$BARU" "$LAMA" || { merah "  ❌ gagal menyalin baru"; exit 1; }
#  WAL/SHM lama milik DB lama — buang supaya tidak bentrok.
rm -f "${LAMA}-wal" "${LAMA}-shm"
hijau "  ✅ diganti"

biru "═══ 6. VERIFIKASI AKHIR ═══"
python3 - "$LAMA" <<'PY'
import sqlite3, sys
c = sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True)
print('  integrity :', c.execute('pragma quick_check').fetchone()[0])
print('  pesan     :', c.execute('select count(*) from messages').fetchone()[0])
c.close()
PY

hijau "═══ SELESAI — Hermes perlu di-restart untuk memakai DB baru ═══"
cat <<'CATATAN'

  LANGKAH TERAKHIR (manual):
    hermes restart        # atau matikan & hidupkan Hermes

  MUNDUR kalau ada masalah:
    cp /opt/data/_siap-tukar-state/state-lama.db /opt/data/state.db
    rm -f /opt/data/state.db-wal /opt/data/state.db-shm
CATATAN
