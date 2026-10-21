#!/usr/bin/env bash
# Bandingkan berkas app/ di HOST vs IMAGE LIVE 04Okt26 — buktikan perubahan = blok satpam saja.
cd /opt/data/services/eduai-publishing || exit 1
IMG=eduai-app:20261004_143446-sot
mkdir -p /tmp/banding
for f in ai.py state.py config.py belajar.py satpam.py; do
  echo "───────── $f ─────────"
  if docker run --rm --entrypoint cat "$IMG" "/app/app/$f" > "/tmp/banding/$f" 2>/dev/null; then
    a=$(md5sum "/tmp/banding/$f" | cut -c1-12); b=$(md5sum "app/$f" 2>/dev/null | cut -c1-12)
    if [ "$a" = "$b" ]; then echo "  SAMA (tidak berubah)"; continue; fi
    echo "  BERUBAH: image=$a host=$b"
    diff -u "/tmp/banding/$f" "app/$f" | head -50
    echo "  (total baris diff: $(diff "/tmp/banding/$f" "app/$f" | grep -c '^[<>]'))"
  else
    echo "  ADA DI HOST, TIDAK ADA DI IMAGE"
    wc -l "app/$f"
  fi
done
