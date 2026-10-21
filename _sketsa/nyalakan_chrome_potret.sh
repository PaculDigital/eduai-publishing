#!/usr/bin/env bash
# Nyalakan Chrome potret di :9333 — LEPAS TOTAL dari sesi ini.
# Jebakan 07Okt26: `nohup ... &` / background Hermes → Chrome ikut mati saat
# proses induk selesai. Solusi: `setsid --fork` (sesi baru, PPID 1).
# ⚠️ 11Okt26: SATU VERSI SAJA (putusan Bos). chromium-152 PRO RUSAK (exit 133
#    Trace/breakpoint trap di semua mode) ⇒ dihapus. chromium-146 TERBUKTI HIDUP.
CHROME="$(ls -d /opt/data/.cloakbrowser/chromium-*/chrome /opt/data/home/.cloakbrowser/chromium-*/chrome 2>/dev/null | sort -V | tail -1)"
[ -z "$CHROME" ] && { echo "GAGAL: tak ada binary chrome"; exit 1; }
PORT=9333
BARU="/tmp/chrome-uji-baru"
pkill -f "remote-debugging-port=$PORT" 2>/dev/null
rm -rf "$BARU"
sleep 1
setsid --fork "$CHROME" --headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --remote-debugging-port=$PORT --remote-allow-origins='*' \
  --user-data-dir="$BARU" --window-size=1180,3900 about:blank \
  </dev/null >/tmp/chrome-uji.log 2>&1
# tunggu sampai benar-benar siap
for i in $(seq 1 25); do
  sleep 1
  if curl -s -m 3 "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
    echo "OK hidup di :$PORT setelah ${i} dtk · PPID=$(ps -o ppid= -p $(pgrep -f "remote-debugging-port=$PORT" | head -1) 2>/dev/null | tr -d ' ')"
    exit 0
  fi
done
echo "GAGAL: port $PORT tidak menjawab"; tail -3 /tmp/chrome-uji.log; exit 1
