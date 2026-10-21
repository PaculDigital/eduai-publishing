#!/usr/bin/env bash
#  Daftar FITUR HIDUP — cek rute & template (07 Okt 2026)
cd /opt/data/services/eduai-publishing || exit 1
echo "=== HALAMAN (template) ==="
ls app/templates/*.html | sed 's|app/templates/||' | tr '\n' ' '
echo; echo
echo "=== RUTE API TERDAFTAR ==="
grep -rn "@router\.\(get\|post\|put\|delete\)" app/rute_*.py | sed 's/.*@router\.//' | sort | uniq -c | sort -rn | head -5
echo
echo "--- per berkas rute ---"
for f in app/rute_*.py; do
  n=$(grep -c "@router\." "$f")
  printf "%-34s %s rute\n" "$(basename $f)" "$n"
done
echo
echo "=== MODUL FITUR (app/*.py inti) ==="
ls app/*.py | sed 's|app/||' | tr '\n' ' '
