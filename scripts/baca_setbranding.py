#!/usr/bin/env python3
"""Baca fungsi setBranding di Header.js — di situ teks 'ONLYOFFICE' berada."""
import subprocess

OO = 'oo-converter'
DS = '/var/www/onlyoffice/documentserver'
H = f'{DS}/web-apps/apps/common/main/lib/view/Header.js'


def sh(cmd, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip()


print("=" * 76)
print("FUNGSI setBranding (Header.js 1149-1215)")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"sed -n '1149,1215p' {H}\""))

print("\n" + "=" * 76)
print("Cari teks ONLYOFFICE / brand di Header.js")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"grep -n 'ONLYOFFICE\\|onlyoffice\\|"
         f"branding\\|Branding' {H} | head -20\""))

print("\n" + "=" * 76)
print("Berkas di resources/img/header")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"ls -la {DS}/web-apps/apps/common/main/"
         f"resources/img/header/ 2>/dev/null\""))
