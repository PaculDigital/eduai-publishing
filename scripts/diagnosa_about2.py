#!/usr/bin/env python3
"""Uji: apakah config kita BENAR terbentuk, dan apakah OO bisa unduh logo?

Juga cek dari SISI OO: apakah oo-converter bisa akses URL logo kita?
"""
import json
import subprocess

CONTAINER = 'eduai-app'
OO = 'oo-converter'


def sh(cmd, timeout=120):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()


print("=" * 76)
print("1. CONFIG YANG KITA BANGUN (isi blok customization)")
print("=" * 76)
out, err = sh(f"""docker exec {CONTAINER} python3 -c "
import json
from app import onlyoffice as o
cfg = o.konfigurasi_editor(
    berkas_id='abc', nama='x.docx', url_unduh='http://x/u', url_simpan='http://x/s',
    user_id=1, user_nama='Uji', mode='edit')
c = cfg['editorConfig']['customization']
print(json.dumps({{k: c[k] for k in c if k in ('about','customer','logo')}},
                 indent=1, ensure_ascii=False))
" 2>&1""")
print(out or err)

print("\n" + "=" * 76)
print("2. BISAKAH oo-converter MENGUNDUH LOGO KITA?")
print("=" * 76)
url = 'https://eduai.bikinaja.id/static/ikon-burung-about.png'
out, err = sh(f"docker exec {OO} sh -c \"wget -q -T 20 -O /tmp/l.png '{url}' "
              f"&& ls -l /tmp/l.png || echo GAGAL\"")
print(f"  dari {OO}: {out or err}")

# juga coba lewat IP container app
out, err = sh(f"docker exec {OO} sh -c \"wget -q -T 10 -O /tmp/l2.png "
              f"'http://172.17.0.8:8000/static/ikon-burung-about.png' "
              f"&& ls -l /tmp/l2.png || echo GAGAL\"")
print(f"  via IP container app: {out or err}")

print("\n" + "=" * 76)
print("3. APAKAH OO MEMBACA customer DARI CONFIG YANG DIKIRIM?")
print("=" * 76)
out, err = sh(f"docker exec {OO} sh -c \"grep -rn 'customization.customer\\|"
              f"customer' /var/www/onlyoffice/documentserver/web-apps/apps/"
              f"api/documents/api.js | head -10\"")
print(out or err)

print("\n" + "=" * 76)
print("4. SIAPA YANG SET publishername DI EDITOR (bukan About.js)")
print("=" * 76)
out, err = sh(f"docker exec {OO} sh -c \"grep -rn 'publishername\\|customer' "
              f"/var/www/onlyoffice/documentserver/web-apps/apps/common/main/lib/"
              f"view/About.js | head -12\"")
print(out or err)
