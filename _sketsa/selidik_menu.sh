#!/usr/bin/env bash
#  Selidiki: halaman mana yang pakai _menu.html (07 Okt 2026)
cd /opt/data/services/eduai-publishing || exit 1
echo "=== template yang MEMANGGIL _menu.html ==="
grep -ln "include '_menu.html'" app/templates/*.html
echo
echo "=== template yang BELUM memanggil (kandidat) ==="
for f in app/templates/*.html; do
  grep -q "include '_menu.html'" "$f" || echo "  $(basename "$f")"
done
echo
echo "=== apakah ada pita tab LAMA yang masih disalin manual? ==="
grep -ln 'class="pita-tab"\|class="pita"' app/templates/*.html
echo
echo "=== menu_aktif yang dipakai ==="
grep -n "set menu_aktif" app/templates/*.html
