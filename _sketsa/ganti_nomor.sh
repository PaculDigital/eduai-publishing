#!/bin/bash
# Ganti nomor WA lama -> baru di ZIP LoA + proyek EduAi
cd /tmp/loa2_x/tridarma-loa || exit 1

echo "== ganti nomor di ZIP =="
for f in verifikasi-loa.html template-loa-jemt.html; do
  sed -i 's/0857-2050-5555/0851-7813-8514/g' "$f"
  echo "  $f -> $(grep -o '085[0-9-]*' "$f" | sort -u | tr '\n' ' ')"
done

echo "== sisa nomor lama di ZIP =="
grep -rn "0857-2050-5555" . || echo "  bersih"

echo "== copy halaman verifikasi ke EduAi =="
mkdir -p /opt/data/services/eduai-publishing/app/templates/loa
cp verifikasi-loa.html /opt/data/services/eduai-publishing/app/templates/loa/verifikasi-loa.html
echo "  ok"

echo "== nomor lama di proyek EduAi =="
grep -rn "0857-2050-5555" /opt/data/services/eduai-publishing/app/ || echo "  bersih"
