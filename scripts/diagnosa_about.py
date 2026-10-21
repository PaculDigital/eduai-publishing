#!/usr/bin/env python3
"""Diagnosa: apakah blok `customer` benar-benar terkirim ke editor OO?

Periksa:
  1. Config yang dibuat app kita (panggil fungsinya langsung)
  2. Apa yang OO terima (cek dari HTML halaman editor)
  3. Apakah OO 9.4.0 mendukung `customization.customer`
"""
import json
import re
import subprocess

CONTAINER = 'eduai-app'


def sh(cmd, timeout=120):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip()


print("=" * 76)
print("1. CONFIG DARI APP KITA — apa blok customer ada?")
print("=" * 76)
out = sh(f"""docker exec {CONTAINER} python3 -c "
import json
from app.onlyoffice import buat_config
import inspect
print([n for n in dir() if 'config' in n.lower()])
" 2>&1 | tail -5""")
print(out)

# cari nama fungsi pembuat config
out = sh(f"""docker exec {CONTAINER} python3 -c "
import app.onlyoffice as o
import inspect
fns=[n for n,o2 in inspect.getmembers(o, inspect.isfunction)]
print('FUNGSI:', fns)
" 2>&1 | tail -5""")
print(out)

print("\n" + "=" * 76)
print("2. cek definisi fungsi config & apakah 'customer' ikut")
print("=" * 76)
out = sh(f"""docker exec {CONTAINER} python3 -c "
import app.onlyoffice as o
import inspect
src=inspect.getsource(o)
i=src.find(\\\"'customer'\\\")
print('customer DITEMUKAN di source' if i>0 else 'customer TIDAK ADA di source')
print('URL_LOGO_ABOUT =', getattr(o,'URL_LOGO_ABOUT','(tidak ada)'))
" 2>&1 | tail -5""")
print(out)

print("\n" + "=" * 76)
print("3. APAKAH OO 9.4.0 MENGENAL customization.customer ?")
print("=" * 76)
out = sh("docker exec oo-converter sh -c \"grep -rl 'customer' "
         "/var/www/onlyoffice/documentserver/web-apps/apps/api/documents/ "
         "--include=*.js 2>/dev/null | head -5\"")
print(f"  berkas api yg menyebut 'customer': {out or '(tidak ada)'}")

out = sh("docker exec oo-converter sh -c \"grep -hoE "
         "'customer[A-Za-z]*' /var/www/onlyoffice/documentserver/web-apps/apps/"
         "common/main/lib/view/About.js | sort -u | head -5\"")
print(f"  di About.js: {out or '(tidak ada)'}")

# cari siapa yang mengisi publishername
out = sh("docker exec oo-converter sh -c \"grep -rn 'publishername' "
         "/var/www/onlyoffice/documentserver/web-apps/apps/common/ "
         "--include=*.js 2>/dev/null | grep -v 'About.js' | head -8\"")
print(f"\n  yang mengisi publishername:\n{out or '(tidak ada)'}")
