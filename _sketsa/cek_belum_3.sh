#!/usr/bin/env bash
#  CEK TELITI bagian 3 — pemicu notifikasi & angka mati (07 Okt 2026)
cd /opt/data/services/eduai-publishing || exit 1

echo "════════ 9b. APAKAH _kuota_hampir_habis DIPANGGIL? ════════"
grep -rn "_kuota_hampir_habis\|kuota_hampir_habis" app/*.py | grep -v "notifikasi.py" | head -5
echo "  (kosong = fungsi ADA tapi tak pernah dipanggil)"
echo
echo "════════ 10. AI_MAX_NASKAH_KARAKTER (angka mati?) ════════"
grep -rn "AI_MAX_NASKAH_KARAKTER" app/*.py
echo
echo "════════ 11. PROMPT DEDUKTIF ════════"
grep -rn "deduktif\|induktif" app/*.py | head -5
echo
echo "════════ 12. KONVERSI: rute POST ada? ════════"
grep -rn "konversi" app/main.py | grep -i "post\|@app" | head -5
echo "  -- fungsi mesin konversi --"
grep -n "^def \|^async def " app/konversi.py | head -20
