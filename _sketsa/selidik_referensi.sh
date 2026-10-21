#!/usr/bin/env bash
#  Selidiki tab Referensi (07 Okt 2026)
cd /opt/data/services/eduai-publishing || exit 1
echo "=== template referensi.html? ==="
if [ -f app/templates/referensi.html ]; then
  wc -c app/templates/referensi.html
else
  echo "  TIDAK ADA"
fi
echo
echo "=== rute referensi di rute_jurnal.py ==="
grep -n "referensi" app/rute_jurnal.py | head -10
echo
echo "=== tab Referensi di template lain ==="
for f in naskah kolaborasi belajar referensi; do
  printf '%-16s %s\n' "$f.html" "$(grep -c 'Referensi' "app/templates/$f.html" 2>/dev/null || echo 'NA')"
done
echo
echo "=== _menu.html punya Referensi? ==="
grep -c "Referensi" app/templates/_menu.html 2>/dev/null || echo "NA"
