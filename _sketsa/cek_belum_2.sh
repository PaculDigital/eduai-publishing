#!/usr/bin/env bash
#  CEK TELITI bagian 2 (07 Okt 2026)
cd /opt/data/services/eduai-publishing || exit 1

echo "════════ 5. PENYARING TANDA SAAT UNDUH ════════"
echo "-- /unduh/{fid} di main.py (baris 921) --"
sed -n '921,935p' app/main.py
echo
echo "-- apakah ada fungsi saring tanda/sorotan? --"
grep -rn "def saring\|def buang_tanda\|def bersihkan_tanda\|def hapus_tanda" app/*.py | head
echo
echo "════════ 6. DUA PEMBIMBING (kolom vs fitur) ════════"
grep -n "pembimbing_1\|pembimbing_2" app/models.py | head -5
echo "-- dipakai di kode lain? --"
grep -rn "pembimbing_1\|pembimbing_2" app/*.py | grep -v models.py | head -5
echo "  (kosong = kolom nganggur)"
echo
echo "════════ 7. INGATAN BAB PENUH ════════"
grep -n "def ingatan\|def memori_bab\|ingatan_bab\|memori_penuh" app/*.py | head -5
echo
echo "════════ 8. BACKUP R2 ════════"
grep -rn "boto3\|import r2\|cloudflare.*r2\|storage.*r2" app/*.py | head -5
echo "  (kosong = belum ada)"
echo
echo "════════ 9. PICUICU NOTIFIKASI KUOTA ════════"
grep -n "def \|kuota.*habis\|sisa.*rendah\|peringatan_kuota" app/notifikasi.py | head -15
