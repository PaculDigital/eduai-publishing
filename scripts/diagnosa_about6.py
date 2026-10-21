#!/usr/bin/env python3
"""KENAPA About masih lama padahal About.js sudah diganti?

Periksa:
  1. File yang BENAR-BENAR dikirim ke browser (via proxy kita /oo/aset)
  2. Apakah ada SALINAN About.js lain di disk
  3. Apakah nginx pakai berkas .gz atau .js
"""
import subprocess

C = 'oo-converter'
DS = '/var/www/onlyoffice/documentserver'


def sh(cmd, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip()


print("=" * 76)
print("1. SEMUA salinan About.js di dalam container")
print("=" * 76)
print(sh(f"docker exec {C} sh -c \"find / -name 'About.js' -not -path "
         f"'/proc/*' 2>/dev/null | head -20\""))

print("\n" + "=" * 76)
print("2. About.js.gz vs About.js — mana yang lebih baru & isinya?")
print("=" * 76)
print(sh(f"docker exec {C} sh -c \"ls -la {DS}/web-apps/apps/common/main/lib/"
         f"view/About.js* 2>/dev/null\""))

print("\n" + "=" * 76)
print("3. Isi HEADER About.js (10 baris pertama) — apakah sudah baru?")
print("=" * 76)
print(sh(f"docker exec {C} sh -c \"grep -n 'EduAi\\|Ascensio' "
         f"{DS}/web-apps/apps/common/main/lib/view/About.js | head -5\""))

print("\n" + "=" * 76)
print("4. APAKAH ada berkas serupa di web-apps/common (versi minified?)")
print("=" * 76)
print(sh(f"docker exec {C} sh -c \"find {DS}/web-apps -name '*.js' "
         f"-newermt '2026-09-12 11:00' 2>/dev/null | head -10\""))

print("\n" + "=" * 76)
print("5. CEK DARI LUAR: apa yang dikirim ke browser lewat proxy kita?")
print("=" * 76)
f = ('/web-apps/apps/common/main/lib/view/About.js')
out = sh(f"docker exec eduai-app python3 -c \""
         f"import urllib.request;"
         f"r=urllib.request.urlopen('https://eduai.bikinaja.id/oo/aset{f}',"
         f"timeout=30);d=r.read();"
         f"import gzip;"
         f"print('status',r.status,'len',len(d));"
         f"print('content-encoding',r.headers.get('Content-Encoding'));"
         f"print('EduAi ADA' if b'EduAi INOVASI' in d else 'EduAi TIDAK ADA');"
         f"print('Ascensio ADA' if b'Ascensio' in d else 'Ascensio TIDAK ADA')\"")
print(out)

print("\n" + "=" * 76)
print("6. CEK cache Cloudflare (kalau HIT, yang lama masih tersimpan!)")
print("=" * 76)
out = sh(f"docker exec eduai-app python3 -c \""
         f"import urllib.request;"
         f"r=urllib.request.urlopen('https://eduai.bikinaja.id/oo/aset{f}',"
         f"timeout=30);"
         f"print('cf-cache-status:', r.headers.get('cf-cache-status'));"
         f"print('age:', r.headers.get('age'));"
         f"print('cache-control:', r.headers.get('cache-control'))\"")
print(out)
