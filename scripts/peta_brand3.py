#!/usr/bin/env python3
"""Cek aset yang PALING terlihat user saat loading: preload, cache-scripts,
favicon, dan logo header editor."""
import subprocess

C = 'oo-converter'
DS = '/var/www/onlyoffice/documentserver'
API = f'{DS}/web-apps/apps/api/documents'


def sh(cmd, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip()


print("=" * 78)
print("1. preload.html — HALAMAN YANG DILIHAT USER SAAT LOADING")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"grep -nE 'logo|img|svg|png|title|OnlyOffice' "
         f"{API}/preload.html | head -25\"")
print(out or '(bersih)')

print("\n" + "=" * 78)
print("2. cache-scripts.html")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"grep -nE 'logo|img|svg|OnlyOffice|title' "
         f"{API}/cache-scripts.html | head -15\"")
print(out or '(bersih)')

print("\n" + "=" * 78)
print("3. api.js — ada teks/URL OnlyOffice?")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"grep -oE 'onlyoffice[a-zA-Z0-9_/.-]*|"
         f'OnlyOffice[a-zA-Z0-9 _.-]*\' {API}/api.js | sort -u | head -20"')
print(out or '(bersih)')

print("\n" + "=" * 78)
print("4. GAMBAR LOADING/SPLASH (yang tampil sebelum editor siap)")
print("=" * 78)
for pola in ['*load*', '*splash*', '*wait*', '*progress*']:
    out = sh(f"docker exec {C} sh -c \"find {DS}/web-apps/apps/api "
             f"{DS}/web-apps/apps/documenteditor/main/resources/img "
             f"-iname '{pola}' -type f 2>/dev/null | head -8\"")
    if out:
        print(f"\n  {pola}:")
        for b in out.split('\n'):
            print(f"    {b}")

print("\n" + "=" * 78)
print("5. LOGO DI HEADER EDITOR (logo-header.svg?)")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"find {DS}/web-apps -iname 'logo*' -type f "
         f"2>/dev/null | grep -v vg\\.gz | wc -l\"")
print(f"  total berkas logo*: {out}")
out = sh(f"docker exec {C} sh -c \"find {DS}/web-apps -path '*api*' -iname '*.svg' "
         f"-o -path '*api*' -iname '*.png' | head -15\"")
print("  aset gambar di folder api:")
for b in (out.split('\n') if out else ['(tidak ada)']):
    print(f"    {b}")

print("\n" + "=" * 78)
print("6. FAVICON — bandingkan dengan logo EduAi (kalau ada)")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"md5sum {DS}/web-apps/apps/documenteditor/main/"
         f"resources/img/favicon.ico {DS}/server/welcome/img/favicon.ico 2>/dev/null\"")
print(out)
out = sh("cd /opt/data/services/eduai-publishing && "
         "find . -iname 'favicon*' -o -iname 'logo*' | grep -v _arsip | head -15")
print("\n  aset brand milik project EduAi:")
for b in (out.split('\n') if out else ['(tidak ada)']):
    print(f"    {b}")
