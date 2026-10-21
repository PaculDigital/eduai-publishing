#!/usr/bin/env python3
"""Cari elemen LOGO di dialog About OO (About.js) — apakah ada default gambar?"""
import subprocess

OO = 'oo-converter'
A = ('/var/www/onlyoffice/documentserver/web-apps/apps/common/main/'
     'lib/view/About.js')


def sh(cmd, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip()


print("=" * 76)
print("1. Bagian atas About.js (30-80) — struktur template")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"sed -n '30,80p' {A}\""))

print("\n" + "=" * 76)
print("2. Cari 'logo' / 'img' / 'image' di About.js")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"grep -n 'logo\\|img\\|image\\|divCompanyLogo' "
         f"{A} | head -20\""))

print("\n" + "=" * 76)
print("3. Fungsi setLicInfo (baris ~200-260)")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"sed -n '200,262p' {A}\""))
