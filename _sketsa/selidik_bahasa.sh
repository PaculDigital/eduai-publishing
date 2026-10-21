#!/usr/bin/env bash
# Selidiki dari mana "English – United States" muncul di editor.
# Hipotesis: (a) dari berkas .docx, (b) dari cache OO, (c) dari config kita.
cd /opt/data/services/eduai-publishing || exit 1

echo "=== 1. Isi Editor.bin (cache OO doc 80): cari bahasa ==="
docker exec oo-converter sh -c 'strings /var/lib/onlyoffice/documentserver/App_Data/cache/files/data/e80v1790940457/Editor.bin 2>/dev/null | grep -iE "lang|en-US|id-ID|English|Indonesia" | head -10'
echo "(kosong = bukan di situ)"

echo
echo "=== 2. Berkas .docx doc 80 (yang user dapat) ==="
docker exec eduai-app python3 -c "
import zipfile, re, collections
p='/app/uploads/7/75ddce8b3e0feaea.docx'
z=zipfile.ZipFile(p)
for n in z.namelist():
    if n.endswith('.xml'):
        d=z.read(n).decode('utf-8','ignore')
        l=re.findall(r'w:lang[^>]*', d)
        t=re.findall(r'<w:themeFontLang[^>]*', d)
        if l or t:
            print(f'  {n}: lang={l} theme={t}')
print('  (kalau di atas id-ID semua, berkas BENAR)')
"

echo
echo "=== 3. Config yang dikirim server untuk doc 80 ==="
T=$(docker exec eduai-app python3 -c "from app.auth import buat_token; print(buat_token(7))")
C=$(docker exec eduai-app python3 -c "from app.config import SESSION_COOKIE; print(SESSION_COOKIE)")
curl -s --max-time 25 -H "Cookie: $C=$T" "https://eduai.bikinaja.id/edit/80" 2>/dev/null \
  | grep -oE '"lang"[^,]*|lang: *.[a-z-]+|&lang=[a-z-]+' | head -5

echo
echo "=== 4. Apakah OO punya daftar bahasa yang diaktifkan? ==="
docker exec oo-converter sh -c 'cat /etc/onlyoffice/documentserver/default.json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); s=d.get(\"services\",{}).get(\"CoAuthoring\",{}); print(json.dumps({k:v for k,v in s.items() if \"ang\" in k}, indent=1))" 2>/dev/null'
echo "(kosong = tidak dibatasi)"
