#!/bin/bash
# Bersihkan sisa nomor lama di SEMUA berkas ZIP LoA
cd /tmp/loa2_x/tridarma-loa || exit 1

echo "== ganti di semua berkas teks =="
for f in gen_docx.py agent/contoh-data-loa.json agent/LoA-001-LOA-JEMT-X-2026.html agent/generate_loa.py agent/template-loa-jemt-agent.html template-loa-jemt.html; do
  if [ -f "$f" ]; then
    sed -i 's/0857-2050-5555/0851-7813-8514/g' "$f"
    echo "  $f"
  fi
done

echo
echo "== SISA nomor lama di SELURUH ZIP =="
grep -rn "0857-2050-5555" . && echo "  !! MASIH ADA" || echo "  BERSIH ✓"

echo
echo "== nomor baru yang terpasang =="
grep -rn "0851-7813-8514" . | sed 's/:.*0851/ -> 0851/' | head -10

echo
echo "== sinkron ke proyek EduAi (template + mesin) =="
D=/opt/data/services/eduai-publishing
cp template-loa-jemt.html $D/app/templates/loa/loa-jemt.html
cp verifikasi-loa.html $D/app/templates/loa/verifikasi-loa.html
cp logo_tridarma.png $D/app/templates/loa/logo-tridarma.png 2>/dev/null
echo "  template + verifikasi + logo disalin"

echo
echo "== cek nomor di proyek EduAi =="
grep -rn "0857-2050-5555" $D/app/ && echo "  !! MASIH ADA" || echo "  BERSIH ✓"
grep -n "contact_wa" $D/app/loa.py
