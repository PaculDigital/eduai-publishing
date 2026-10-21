#!/bin/bash
# UJI NYATA: halaman verifikasi lewat domain qr.tridarma.id + API
echo "══ 1. DNS qr.tridarma.id ══"
getent hosts qr.tridarma.id || echo "  (belum resolve)"

echo
echo "══ 2. Halaman verifikasi (qr.tridarma.id) ══"
curl -s -o /tmp/verif.html -w "  http_code=%{http_code}  ukuran=%{size_download} byte  waktu=%{time_total}s\n" https://qr.tridarma.id/verifikasi-loa

echo
echo "══ 3. API cek nomor (qr.tridarma.id) ══"
curl -s -w "\n  http_code=%{http_code}\n" "https://qr.tridarma.id/api/loa/cek?no=1.001"

echo
echo "══ 4. API cek nomor PALSU ══"
curl -s -w "\n  http_code=%{http_code}\n" "https://qr.tridarma.id/api/loa/cek?no=9.999"

echo
echo "══ 5. apakah halaman memuat QR + judul? ══"
grep -o "VERIFIKASI\|Verifikasi LoA\|Nomor LoA" /tmp/verif.html | sort -u | head -5

echo
echo "══ 6. EduAi utama masih sehat? ══"
curl -s -o /dev/null -w "  eduai.bikinaja.id/health = %{http_code}\n" https://eduai.bikinaja.id/health
curl -s -o /dev/null -w "  tridarma.id = %{http_code}\n" https://tridarma.id
