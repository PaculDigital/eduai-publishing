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
# Backup DB eduai (checkpoint WAL -> docker cp -> verify)
set -uo pipefail
cd /opt/data/services/eduai-publishing
DIR=_arsip/pre-sesi-20260912-034045
mkdir -p "$DIR"

echo "=== 1. Checkpoint WAL ==="
docker exec eduai-app /usr/local/bin/python -c "
import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
print('  checkpoint OK')
c.close()
"

echo "=== 2. Copy DB + WAL + SHM ==="
docker cp eduai-app:/app/data/eduai.db     "$DIR/eduai.db"     2>&1 | tail -1
docker cp eduai-app:/app/data/eduai.db-wal "$DIR/eduai.db-wal" 2>&1 | tail -1
docker cp eduai-app:/app/data/eduai.db-shm "$DIR/eduai.db-shm" 2>&1 | tail -1

echo "=== 3. Verifikasi isi backup ==="
/opt/data/.venv/bin/python3 - <<'PY'
import sqlite3
c = sqlite3.connect('_arsip/pre-sesi-20260912-034045/eduai.db')
t = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print(f'  tabel    : {t}')
print(f'  users    : {c.execute("SELECT COUNT(*) FROM users").fetchone()[0]}')
print(f'  files    : {c.execute("SELECT COUNT(*) FROM files").fetchone()[0]}')
print(f'  transaksi: {c.execute("SELECT COUNT(*) FROM transaksi").fetchone()[0]}')
c.close()
PY

echo "=== 4. Daftar backup ==="
ls -la "$DIR"
