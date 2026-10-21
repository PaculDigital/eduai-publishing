#!/bin/bash
# Bereskan 2 temuan gerbang: B3 (nama berkas) + B5 (skrip di /tmp)
D=/opt/data/services/eduai-publishing
S=$D/_sketsa

echo "== B3: ganti nama berkas bantu (bukan 'baru') =="
if [ -f "$S/uji_template_baru.py" ]; then
  mv "$S/uji_template_baru.py" "$S/uji_isi_template_loa.py"
  echo "   uji_template_baru.py -> uji_isi_template_loa.py"
fi

echo
echo "== B5: pindahkan skrip nyasar dari /tmp =="
for f in /tmp/potret_cdp.py /tmp/potret_lokal_kerja.py; do
  if [ -f "$f" ]; then
    mv "$f" "$S/$(basename $f)"
    echo "   $f -> _sketsa/$(basename $f)"
  fi
done

echo
echo "== sisa di /tmp =="
ls /tmp/potret_cdp.py /tmp/potret_lokal_kerja.py 2>/dev/null || echo "   bersih"
