#!/usr/bin/env bash
# GERBANG BAHASA DOKUMEN — jaga templat naskah-baru.docx tetap BERBAHASA INDONESIA.
# Akar (02Okt26): styles.xml templat berisi w:lang w:val="en-US" → tiap dokumen
# BARU lahir berbahasa Inggris (dropdown "English - United States" di editor).
# OnlyOffice: bahasa dokumen = properti berkas, TIDAK bisa lewat Docs API →
# satu-satunya jalan resmi = benarkan templat.
set -u
cd "$(dirname "$0")/.." || exit 1
T="app/templat/naskah-baru.docx"
L=0; G=0
lulus(){ echo "LULUS  : $1"; L=$((L+1)); }
gagal(){ echo "GAGAL  : $1"; G=$((G+1)); }

echo "GERBANG BAHASA DOKUMEN — $(date '+%d %b %Y %H:%M')"
echo
echo "═══ 1. Templat ada & sehat ═══"
if [ -f "$T" ]; then lulus "templat ADA ($(stat -c%s "$T") byte)"; else gagal "templat TIDAK ADA"; fi

echo
echo "═══ 2. Bahasa di dalam templat (wajib id-ID) ═══"
BAHASA=$(python3 - "$T" <<'PY'
import sys, zipfile, re, collections
p = sys.argv[1]
try:
    z = zipfile.ZipFile(p)
    hasil = collections.Counter()
    for n in z.namelist():
        if n.endswith('.xml'):
            d = z.read(n).decode('utf-8', 'ignore')
            for m in re.findall(r'w:lang w:val="([^"]+)"', d):
                hasil[m] += 1
    print(','.join(sorted(hasil)) if hasil else 'KOSONG')
except Exception as e:
    print('GALAT:' + type(e).__name__)
PY
)
echo "   bahasa terdeteksi: $BAHASA"
case "$BAHASA" in
  *en-US*) gagal "templat MASIH berbahasa en-US (dokumen baru akan berbahasa Inggris)" ;;
  *id-ID*|*"id"*) lulus "templat berbahasa Indonesia ($BAHASA)" ;;
  *) gagal "bahasa templat tidak dikenali: $BAHASA" ;;
esac

echo
echo "═══ 3. Berkas DIBUAT dari templat → bahasanya ikut ═══"
SEMENTARA="/tmp/uji-bahasa-$$.docx"
cp "$T" "$SEMENTARA" 2>/dev/null
if [ -f "$SEMENTARA" ]; then
  H=$(python3 - "$SEMENTARA" <<'PY'
import sys, zipfile, re, collections
z = zipfile.ZipFile(sys.argv[1])
d = z.read('word/styles.xml').decode('utf-8', 'ignore')
c = collections.Counter(re.findall(r'w:lang w:val="([^"]+)"', d))
print('en' if any(k.startswith('en') for k in c) else 'id')
PY
)
  [ "$H" = "id" ] && lulus "dokumen baru mewarisi bahasa Indonesia" \
                  || gagal "dokumen baru masih berbahasa Inggris (warisan templat salah)"
  rm -f "$SEMENTARA"
else
  gagal "gagal menyalin templat untuk uji"
fi

echo
echo "═══ 4. Templat yang DIPAKAI PRODUKSI (di image/container) ═══"
if docker exec eduai-app test -f /app/app/templat/naskah-baru.docx 2>/dev/null; then
  PB=$(docker exec eduai-app python3 -c "
import zipfile,re,collections
z=zipfile.ZipFile('/app/app/templat/naskah-baru.docx')
d=z.read('word/styles.xml').decode('utf-8','ignore')
print(dict(collections.Counter(re.findall(r'w:lang w:val=\"([^\"]+)\"', d))))
" 2>/dev/null)
  echo "   produksi: $PB"
  case "$PB" in
    *en-US*) gagal "PRODUKSI masih en-US → perbaikan BELUM DEPLOY" ;;
    *id*)    lulus "PRODUKSI sudah Indonesia" ;;
    *)       gagal "produksi tidak bisa dibaca" ;;
  esac
else
  gagal "templat tidak ada di container produksi"
fi

echo
echo "HASIL: $L LULUS / $G GAGAL"
[ "$G" -eq 0 ] || exit 1
