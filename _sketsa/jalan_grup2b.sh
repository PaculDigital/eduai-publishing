#!/usr/bin/env bash
#  Jalankan grup 2b (10 berkas uji Tahap 2 + 2.5 + 2.5b + 3.1).
cd /opt/data/services/eduai-publishing || exit 1
L=0; G=0
: > /tmp/grup2b.txt
for f in _uji_pembimbing.py _uji_pembimbing_http.py _uji_bagikan.py \
         _uji_lampiran.py _uji_log_revisi.py _uji_tahan_gempa_tinjau.py \
         _uji_kelompok_bab.py _uji_presisi_dropdown_http.py \
         _uji_luncur_naskah.py _uji_sorotan.py; do
  docker cp "$f" eduai-app:/app/ >/dev/null 2>&1
  out=$(docker exec -w /app eduai-app python3 "$f" 2>&1); rc=$?
  ring=$(printf '%s' "$out" | grep -oE '[0-9]+ *(LULUS|OK)' | tail -1)
  if [ $rc -eq 0 ]; then
    L=$((L+1)); printf '  ✅ %-34s %s\n' "$f" "$ring" >> /tmp/grup2b.txt
  else
    G=$((G+1)); printf '  ❌ %-34s (exit %d)\n' "$f" "$rc" >> /tmp/grup2b.txt
  fi
done
echo "──────── GRUP 2b: $L LULUS / $G GAGAL ────────" >> /tmp/grup2b.txt
