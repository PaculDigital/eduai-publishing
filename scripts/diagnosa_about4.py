#!/usr/bin/env python3
"""Lihat SYARAT di sekitar baris 1472 Main.js (kenapa About pakai default)."""
import subprocess

OO = 'oo-converter'
F = ('/var/www/onlyoffice/documentserver/web-apps/apps/documenteditor/'
     'main/app/controller/Main.js')


def sh(cmd, timeout=120):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip()


print("=" * 76)
print("KONTEKS sekitar baris 1472 (syarat pemanggilan setLicInfo)")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"sed -n '1440,1490p' {F}\""))

print("\n" + "=" * 76)
print("CARI kata 'customer' / 'about' di Main.js")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"grep -n 'customer\\|customization.about\\|"
         f"\\.about' {F} | head -20\""))
