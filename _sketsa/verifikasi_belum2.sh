#!/usr/bin/env bash
#  VERIFIKASI TELITI bagian 2 (07 Okt 2026)
cd /opt/data/services/eduai-publishing || exit 1

echo "════════ B2. SARING TANDA — apa yang 'saring' di main.py? ════════"
grep -n "saring\|buang_tanda\|bersihkan_tanda" app/main.py
echo
echo "════════ D2. PEMICU NOTIF — apakah notifikasi.catat dipanggil? ════════"
grep -rn "notifikasi.catat\|_notif.catat\|from .notifikasi import" app/*.py | head -8
echo
echo "════════ D3. kuota_hampir_habis — ada pemicu? ════════"
grep -rn "hampir_habis\|kuota_menipis\|sisa <= \|sisa <=" app/kuota.py app/proses.py app/ai.py | head -8
echo
echo "════════ F. TOMBOL MULAI KONVERSI (POST) ════════"
grep -rn "konversi" app/main.py | head -8
echo
echo "════════ G. FUNGSI MATI — cek apakah benar 'tak terpakai' ════════"
echo "-- AI_MAX_NASKAH_KARAKTER --"
grep -rn "AI_MAX_NASKAH_KARAKTER" app/*.py
echo "-- apakah config itu dipakai lewat variabel lain? --"
sed -n '135,145p' app/config.py
