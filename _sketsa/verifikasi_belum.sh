#!/usr/bin/env bash
#  VERIFIKASI TELITI — hanya klaim yang bisa DIBUKTIKAN (07 Okt 2026)
#  Aturan Bos: jangan percaya dokumen/ingatan. Setiap klaim HARUS ada bukti kode.
cd /opt/data/services/eduai-publishing || exit 1

echo "════════ A. AGENT PENILAI REVISI (Langkah 4) ════════"
echo "-- apakah hasil revisi AI diperiksa lagi setelah ditulis? --"
grep -rn "periksa_hasil\|nilai_hasil\|cek_hasil_revisi" app/ai.py app/tulis_docx.py app/proses.py app/revisi*.py 2>/dev/null | head -5
echo "  (kosong = tidak ada pemeriksa hasil revisi)"
echo "-- periksa_hasil() di konversi.py itu untuk APA? --"
sed -n '947,960p' app/konversi.py
echo
echo "════════ B. SARING TANDA SAAT UNDUH ════════"
grep -c "saring\|buang_tanda\|bersihkan_tanda" app/main.py app/tulis_docx.py app/sorotan.py
echo "-- fungsi sorotan.py --"
grep -n "^def \|^    def " app/sorotan.py | head -12
echo
echo "════════ C. DUA PEMBIMBING — dipakai di UI? ════════"
grep -rn "pembimbing_1\|pembimbing_2" app/templates/*.html | head -5
echo "  (kosong = tak ada di tampilan)"
echo
echo "════════ D. PEMICU NOTIF KUOTA ════════"
grep -rn "notifikasi\.\|_kuota_hampir_habis\|kirim_notif" app/kuota.py app/proses.py app/ai.py | head -8
echo
echo "════════ E. HASIL REVISI DIPERIKSA AI LAGI? (grep luas) ════════"
grep -rn "periksa.*revisi\|revisi.*periksa\|mutu_revisi" app/*.py | head -5
echo "  (kosong = belum ada)"
