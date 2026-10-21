#!/usr/bin/env bash
# Pelontar uji Opsi D — server VITIASI :8001 di dalam container eduai-app,
# memakai SALINAN kode + SALINAN DB + SALINAN berkas.
# Produksi TIDAK disentuh sama sekali (DB & uploads berbeda).
set -euo pipefail

PROYEK=/opt/data/services/eduai-publishing
CT=eduai-app
PORT=8001
ROOT=/tmp/ujiD_root
DATA=/tmp/ujiD_data
UP=/tmp/ujiD_up

echo "=== 1. bunuh SEMUA server vitiasi sisa, baru hapus salinan ==="
# 🚨 Pelajaran 29Sep26: container TIDAK punya `kill`/`ps`; kode python `-c`
#    inline GAGAL menemukan proses karena cmdline argumen dipisah NUL
#    ('--port\x008001' ≠ '--port 8001') → cuma bungkus `sh` yang mati,
#    anaknya (uvicorn) yatim tetap hidup → pegang inode DB terhapus → 404 palsu.
#    SEKARANG: kode mati ada di BERKAS (sudah diperbaiki NUL-nya).
docker cp $PROYEK/_sketsa/matikan_8001.py $CT:/tmp/matikan_8001.py
docker cp $PROYEK/_sketsa/server_vitiasi.py $CT:/tmp/server_vitiasi.py
docker exec $CT python3 /tmp/matikan_8001.py $PORT || true
sleep 2
docker exec $CT sh -c "rm -rf $ROOT $DATA $UP" || true
# Gerbang: port WAJIB benar-benar tertutup sebelum salinan dihapus.
# (Kalau masih terbuka → ada server sisa → semua hasil uji nanti = 404 PALSU.)
if ! docker exec $CT python3 -c "
import socket, sys
s = socket.socket(); rc = s.connect_ex(('127.0.0.1', $PORT)); s.close()
sys.exit(0 if rc == 111 else 1)"; then
  echo "FATAL: port $PORT masih terbuka setelah pembersihan"; exit 1
fi
echo "port $PORT tertutup ✓"

echo "=== 2. salin KODE dari repo (sumber kebenaran di host) ==="
docker exec $CT sh -c "mkdir -p $ROOT $DATA $UP"
docker cp $PROYEK/app $CT:$ROOT/app
# PROMPTS_DIR = <root>/prompts (ai.py:338) — WAJIB ikut disalin
docker cp $PROYEK/prompts $CT:$ROOT/prompts
docker cp $PROYEK/_arsip/vd_file78.txt $CT:$ROOT/vd_file78.txt
docker cp $PROYEK/_uji_opsiD.py $CT:$ROOT/_uji_opsiD.py

echo "=== 3. salin DB (backup API, konsisten) + berkas ==="
docker exec $CT sh -c "mkdir -p $DATA $UP"
docker exec $CT python3 -c "
import sqlite3
s = sqlite3.connect('/app/data/eduai.db')
d = sqlite3.connect('$DATA/eduai.db')
s.backup(d); d.close(); s.close()
print('DB disalin')"
docker exec $CT sh -c "cp -a /app/uploads/. $UP/"

echo "=== 4. luncurkan server vitiasi :$PORT ==="
# ⚠️ log.app di produksi level 30 (WARNING) → log.info Opsi D tak tercatat.
#    Uji BUTUH jejak `pendamping pipa DIPAKAI` → server vitiasi dijalankan
#    dengan root logger INFO + handler. (Produksi TIDAK diubah.)
docker exec -d $CT sh -c "cd $ROOT && PYTHONPATH=$ROOT EDUAI_DATA_DIR=$DATA \
EDUAI_UPLOAD_DIR=$UP python3 /tmp/server_vitiasi.py $PORT > $ROOT/server.log 2>&1"

echo "=== 5. tunggu /health + BUKTIKAN server ini yang BARU ==="
for i in $(seq 1 25); do
  if docker exec $CT python3 -c "
import urllib.request,sys
try:
    print(urllib.request.urlopen('http://127.0.0.1:$PORT/health',timeout=3).status)
except Exception as e:
    sys.exit(1)" 2>/dev/null; then
    echo "server hidup (percobaan $i)"; break
  fi
  [ "$i" = 25 ] && { echo "GAGAL hidup — log:"; docker exec $CT tail -40 $ROOT/server.log; exit 1; }
  sleep 3
done
# jebakan 29Sep26: bind gagal "address already in use" tapi /health tetap
# 200 dari server LAMA → uji jalan di DB/salinan yang salah.
if docker exec $CT grep -q 'address already in use' $ROOT/server.log; then
  echo "FATAL: port bentrok — server LAMA masih hidup"; exit 1
fi
echo "log server BARU OK (tanpa bentrok port)"
# bukti server BARU benar-benar mengikat port (penanda buatan, bukan banner
# uvicorn yang hilang karena log_config=None). Penanda ditulis oleh utas yang
# tidur dulu 0,5 dtk → beri kesempatan (loop, jangan sekali tembak).
TERIKAT=0
for j in $(seq 1 15); do
  if docker exec $CT grep -q "VITIASI TERIKAT $PORT" $ROOT/server.log; then
    TERIKAT=1; break
  fi
  sleep 1
done
if [ "$TERIKAT" != "1" ]; then
  echo "FATAL: server baris baru TIDAK pernah mengikat port — log:"; exit 1
fi
echo "server BARU terikat port $PORT ✓"

echo "=== 6. jalankan uji ==="
set +e
docker exec -e UJI_BASE=http://127.0.0.1:$PORT \
  -e UJI_DB=$DATA/eduai.db \
  -e UJI_UPLOAD=$UP \
  -e UJI_SRC=$ROOT \
  -e UJI_LOG=$ROOT/server.log \
  -e UJI_VD78=$ROOT/vd_file78.txt \
  $CT python3 $ROOT/_uji_opsiD.py
KODE=$?
set -e

echo "=== 7. buktikan kode baru benar-benar dipakai (jejak log) ==="
docker exec $CT grep -c "OPSI D" $ROOT/server.log || true

echo "=== 8. matikan server vitiasi ==="
docker exec $CT python3 /tmp/matikan_8001.py $PORT || true
sleep 1
# 🚨 JANGAN pakai `grep -q` di sini: `set -o pipefail` + grep yang keluar
#    lebih dulu = docker exec kena SIGPIPE (141) → dianggap GAGAL PALSU.
SISA_TEKS=$(docker exec $CT python3 /tmp/matikan_8001.py $PORT)
case "$SISA_TEKS" in
  *": 0"*) echo "sisa proses port $PORT: 0 (bersih)" ;;
  *) echo "PERINGATAN: masih ada sisa server vitiasi"; echo "$SISA_TEKS"; exit 1 ;;
esac

if [ "$KODE" = "0" ]; then
  docker exec $CT sh -c "rm -rf $ROOT $DATA $UP" || true
  echo "salinan uji dibersihkan"
else
  echo "UJI GAGAL — salinan dibiarkan untuk diagnosis:"
  echo "  kode:   $ROOT/app"
  echo "  db:     $DATA/eduai.db"
  echo "  log:    $ROOT/server.log"
fi

echo "EXIT_UJI=$KODE"
exit $KODE
