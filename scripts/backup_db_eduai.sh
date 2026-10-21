#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════
#  BACKUP DB EDUAI — terjadwal (cron). Bos ACC 03Okt26 (opsi 2-A).
#
#  KENAPA: sebelum ini EduAi TIDAK punya backup DB terjadwal. Backup hanya
#  dibuat saat deploy. Kalau DB rusak di antara dua deploy, data mahasiswa
#  HILANG. Skrip ini menutup celah itu.
#
#  APA YANG DILAKUKAN:
#    1. checkpoint WAL (supaya backup berisi data terbaru, bukan WAL kosong)
#    2. salin eduai.db → _arsip/backup-db/eduai-<waktu>.db
#    3. buang backup LAMA (sisakan N terbaru)
#    4. catat hasil ke log
#
#  CARA PASANG (cron harian 03:00 UTC = 10:00 WIB):
#     0 3 * * * /opt/data/services/eduai-publishing/scripts/backup_db_eduai.sh \
#               >> /opt/data/services/eduai-publishing/_arsip/backup-db/cron.log 2>&1
#
#  SIFAT: TIDAK PERNAH mengganggu aplikasi (baca-saja + copy). Gagal = catat,
#  bukan crash. Tidak butuh docker (DB di bind-mount).
# ══════════════════════════════════════════════════════════════════════════
set -uo pipefail

DIR="/opt/data/services/eduai-publishing"
CONTAINER="eduai-app"
DB="$DIR/data/eduai.db"
OUT="$DIR/_arsip/backup-db"
SIMPAN=14                     # sisakan 14 backup terbaru (~2 minggu harian)
WAKTU="$(date -u +%Y%m%d-%H%M%S)"

mkdir -p "$OUT"

# ── 0. PILIH SUMBER: container ATAU host ─────────────────────────────────
#  ⚠️ PELAJARAN 03Okt26: bind-mount `/app/data` TERBUKTI TIDAK MENEMBUS ke
#  `$DIR/data` (inode beda; menulis dari container tidak muncul di host).
#  Jadi DB ASLI hanya ada DI DALAM container. Baca dari container dulu;
#  pakai berkas host hanya kalau container tidak jalan.
SUMBER=""
if docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  SUMBER="container"
elif [ -s "$DB" ]; then                 # ada isinya (bukan 0 byte)
  SUMBER="host"
fi

if [ -z "$SUMBER" ]; then
  echo "[$(date -u +%FT%TZ)] GAGAL: container '$CONTAINER' tidak jalan DAN $DB kosong/tidak ada"
  exit 1
fi

TUJUAN="$OUT/eduai-$WAKTU.db"

if [ "$SUMBER" = "container" ]; then
  #  checkpoint WAL di dalam container, lalu salin keluar
  docker exec "$CONTAINER" /usr/local/bin/python -c "
import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
c.close()
" 2>/dev/null || echo "[$(date -u +%FT%TZ)] catatan: checkpoint WAL dilewati"
  if ! docker cp "$CONTAINER:/app/data/eduai.db" "$TUJUAN" 2>/dev/null; then
    echo "[$(date -u +%FT%TZ)] GAGAL: docker cp dari $CONTAINER"
    exit 1
  fi
else
  cp "$DB" "$TUJUAN" || { echo "[$(date -u +%FT%TZ)] GAGAL: salin host"; exit 1; }
fi

# ── 1. VERIFIKASI isi (bukan 0 byte / bukan DB rusak) ────────────────────
VERIF="$(python3 - "$TUJUAN" <<'PY' 2>/dev/null
import sqlite3, sys
try:
    c = sqlite3.connect(sys.argv[1])
    n = c.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    c.close()
    print(n)
except Exception:
    print(0)
PY
)"
UKURAN="$(stat -c%s "$TUJUAN" 2>/dev/null || echo 0)"

if [ "${VERIF:-0}" -lt 5 ]; then
  echo "[$(date -u +%FT%TZ)] ⚠️ VERIFIKASI GAGAL — $TUJUAN cuma ${VERIF:-0} tabel, ${UKURAN} byte → DIHAPUS"
  rm -f "$TUJUAN"
  exit 1
fi

MD5="$(md5sum "$TUJUAN" | cut -d' ' -f1)"
echo "[$(date -u +%FT%TZ)] OK $TUJUAN (sumber=$SUMBER, ${UKURAN} byte, ${VERIF} tabel, md5 ${MD5:0:12})"

# ── 3. Buang backup LAMA (sisakan $SIMPAN terbaru) ───────────────────────
#  Urut nama = urut waktu (format YYYYmmdd-HHMMSS) → aman diurutkan nama.
JUMLAH="$(ls -1 "$OUT"/eduai-*.db 2>/dev/null | wc -l)"
if [ "$JUMLAH" -gt "$SIMPAN" ]; then
  ls -1 "$OUT"/eduai-*.db | sort | head -n "$((JUMLAH - SIMPAN))" | while read -r lama; do
    rm -f "$lama"
    echo "[$(date -u +%FT%TZ)] buang lama: $(basename "$lama")"
  done
fi

# ── 4. Laporkan sisa ─────────────────────────────────────────────────────
SISA="$(ls -1 "$OUT"/eduai-*.db 2>/dev/null | wc -l)"
TOTAL="$(du -sh "$OUT" 2>/dev/null | cut -f1)"
echo "[$(date -u +%FT%TZ)] selesai — $SISA backup tersimpan (${TOTAL})"
