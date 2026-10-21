#!/usr/bin/env bash
# CEK BENTROK: mahasiswa vs pembimbing dipakai BERSAMAAN
# Pertanyaan Bos: "semua fitur pembimbing dan mahasiswa tidak bentrok kan?"
cd /opt/data/services/eduai-publishing || exit 1

echo "=== 1. DUA PINTU BERBEDA? ==="
echo "  [Mahasiswa] editor OO penuh  -> rute /edit/{fid} + iframe DocsAPI"
echo "  [Pembimbing] naskah HTML     -> rute /tinjau/{token}/naskah/{berkas_id}"
echo
docker exec eduai-app python3 -c "
from app.main import app
for x in app.routes:
    if not hasattr(x,'path'): continue
    p = x.path
    if p.startswith('/edit') or 'naskah' in p or 'oo/simpan' in p:
        print('  ', ','.join(sorted(getattr(x,'methods',[]) or [])), p)
"

echo
echo "=== 2. SIAPA YANG BOLEH SIMPAN ke berkas (titik bentrok paling bahaya) ==="
docker exec eduai-app python3 -c "
from app.main import app
for x in app.routes:
    if hasattr(x,'path') and '/oo/simpan' in x.path:
        print('  rute simpan:', x.path)
"
grep -n 'def oo_simpan' -A 25 app/main.py | grep -nE 'token|berkas|user|uid|cek|403|valid' | head -12

echo
echo "=== 3. MODE EDITOR: pembimbing dapat 'view' atau 'edit'? ==="
grep -n "def tipe_dokumen" -A 12 app/onlyoffice.py
echo
echo "=== Pemanggil konfigurasi_editor: hanya SATU (main.py:1614)? ==="
grep -rn 'konfigurasi_editor' app/*.py app/templates/*.html 2>/dev/null

echo
echo "=== 4. Apakah pembimbing punya akses /edit/{fid}? (uji pagar) ==="
grep -n "def halaman_editor\|def edit" -A 30 app/main.py | grep -nE 'wajib_login|pemilik|user_id|403|404|milik' | head -10
