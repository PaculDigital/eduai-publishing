#!/usr/bin/env python3
"""Lanjutan: ganti supportemail & phonenum di About.js (+ .gz).

Nama field BENAR di About.js:
  publishername / publisheraddr / publisherurl / supportemail / phonenum
"""
import base64
import gzip
import re
import subprocess
import sys
from pathlib import Path

C = 'oo-converter'
F = ('/var/www/onlyoffice/documentserver/web-apps/apps/common/main/lib/view/'
     'About.js')
ARSIP = Path('/opt/data/services/eduai-publishing/_arsip/oo-about-asli')

BARU = {
    'supportemail': 'eduai@bikinaja.id',
    'phonenum': '+6281-000-000',
}


def sh(cmd, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.returncode, r.stdout.strip()


def baca(path):
    kode, out = sh(f"docker exec {C} sh -c \"base64 -w0 '{path}'\"")
    return base64.b64decode(out) if kode == 0 and out else None


def tulis(path, data):
    b64 = base64.b64encode(data).decode()
    kode, out = sh(f"docker exec {C} python3 -c \"import base64,sys;"
                   f"open('{path}','wb').write(base64.b64decode(sys.argv[1]))\" "
                   f"'{b64}'")
    return kode == 0


print("=" * 76)
print("GANTI supportemail & phonenum di About.js")
print("=" * 76)

# pastikan backup ada (kalau belum, buat dari file SEKARANG bukan ideal —
# tapi file asli sudah ada di ARSIP dari langkah sebelumnya)
(ARSIP / 'About.js').exists() or sys.exit('❌ backup asli tidak ada!')

isi = baca(F)
teks = isi.decode('utf-8', 'replace')
print(f"\nukuran sekarang: {len(isi):,} B")

print("\n[nilai lama]")
for k in BARU:
    m = re.search(rf"{k}\s*:\s*'([^']*)'", teks)
    print(f"  {k:14s} = {m.group(1) if m else '(?)'}")

baru_teks = teks
tot = 0
for k, v in BARU.items():
    baru_teks, n = re.subn(rf"({k}\s*:\s*')([^']*)(')", rf"\g<1>{v}\g<3>",
                           baru_teks)
    print(f"  ganti {k:14s} -> {v}  ({n}x)")
    tot += n

if tot == 0:
    sys.exit('❌ tidak ada penggantian')

data = baru_teks.encode()
print(f"\nukuran baru: {len(data):,} B")

print("\n[tulis .js]", "✅" if tulis(F, data) else "❌")
gz = gzip.compress(data, compresslevel=9, mtime=0)
print("[tulis .gz]", "✅" if tulis(F + '.gz', gz) else "❌")

print("\n[VERIFIKASI — baca 5 field dari .js]")
kode, out = sh(f"docker exec {C} sh -c \"grep -oE "
               f"\\\"(publishername|publisheraddr|publisherurl|supportemail|"
               f"phonenum)\\\\s*:\\\\s*'[^']*'\\\" '{F}'\"")
print(out)

print("\n[VERIFIKASI — isi .gz (yang dikirim nginx)]")
kode, out = sh(f"docker exec {C} python3 -c \"import gzip,re;"
               f"d=gzip.open('{F}.gz','rt',errors='replace').read();"
               f"print(re.findall(r\\\"(publishername|publisheraddr|"
               f"publisherurl|supportemail|phonenum)\\s*:\\s*'([^']*)'\\\", d))\"")
print(out)

print("\n[VERIFIKASI — masih ada 'Ascensio'/'onlyoffice'?]")
kode, out = sh(f"docker exec {C} sh -c \"grep -c 'Ascensio\\|onlyoffice' "
               f"'{F}' || echo 0\"")
print(f"  jumlah kecocokan: {out}")
