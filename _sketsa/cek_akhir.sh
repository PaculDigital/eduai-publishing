#!/usr/bin/env bash
#  CEK AKHIR — daftar BELUM yang benar-benar terbukti (07 Okt 2026)
cd /opt/data/services/eduai-publishing || exit 1

echo "════ 1. TOMBOL/POST KONVERSI — benar belum? ════"
grep -n "@app.post.*konversi\|@app.post.*artikel" app/main.py || echo "  ❌ TIDAK ADA POST konversi"
echo "-- fungsi mesin yang SUDAH siap (menunggu tombol) --"
grep -n "def susun_pesan\|def simpan_hasil\|def periksa_sebelum_konversi" app/konversi.py
echo
echo "════ 2. HASIL REVISI DIPERIKSA LAGI? ════"
grep -n "def " app/proses.py | head -20
echo
echo "════ 3. INGATAN BAB (bukan sub-bab) ════"
grep -n "class .*Bab\|class .*Ingatan\|class SectionState\|class RevisiHistory" app/models.py
echo
echo "════ 4. LOGIN GOOGLE/OTP — cek tabel & rute ════"
grep -n "@app.post('/daftar')" -A 12 app/main.py | grep -i "google\|otp\|verifikasi" || echo "  ❌ daftar manual saja"
echo
echo "════ 5. DUA PEMBIMBING — di UI? ════"
grep -rn "pembimbing_1\|pembimbing_2" app/templates/ | wc -l
echo
echo "════ 6. AI_MAX_NASKAH_KARAKTER benar mati? ════"
grep -rn "AI_MAX_NASKAH_KARAKTER" app/ | wc -l
echo "  (2 = hanya import + definisi, 0 pemakaian)"
