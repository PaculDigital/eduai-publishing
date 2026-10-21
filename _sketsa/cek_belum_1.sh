#!/usr/bin/env bash
#  CEK TELITI: apa yang BENAR-BENAR BELUM (07 Okt 2026)
#  Aturan: setiap tuduhan "belum" HARUS ada bukti kode.
cd /opt/data/services/eduai-publishing || exit 1
echo "════════ 1. AGENT PENILAI REVISI (Langkah 4) ════════"
echo "-- berkas yang mungkin --"
ls app/*penilai* app/*revisi* 2>/dev/null || echo "  (tak ada berkas namanya)"
echo "-- apakah ai.py punya pemeriksa hasil revisi? --"
grep -cn "periksa_hasil\|nilai_revisi\|penilai_revisi" app/ai.py
echo "-- satpam.py fungsi --"
grep -n "^def \|^    def " app/satpam.py | head -20
echo
echo "════════ 2. TELEGRAM / WA (Langkah 6) ════════"
echo "-- modul wa.py ada? --"
ls -la app/wa.py 2>/dev/null && grep -n "^def \|X-Internal-Key\|api/chat" app/wa.py | head -10
echo "-- apakah wa.py benar-benar DIPAKAI di jalur produksi? --"
grep -rn "from .wa import\|from app.wa import\|import wa" app/*.py | grep -v "^app/wa.py" | head -10
echo
echo "════════ 3. LOGIN GOOGLE / OTP ════════"
grep -rn "google.*oauth\|oauth.*google\|client_id.*google\|verify_otp\|kirim_otp" app/*.py | head -6
echo "  (kosong = belum ada)"
echo
echo "════════ 4. MODE BELAJAR FASE A ════════"
grep -n "^def \|^async def " app/belajar.py | head -20
