#!/usr/bin/env python3
"""Lihat baris 1805-1815 Main.js: syarat canBranding & apa yang terjadi."""
import subprocess

OO = 'oo-converter'
F = ('/var/www/onlyoffice/documentserver/web-apps/apps/documenteditor/'
     'main/app/controller/Main.js')


def sh(cmd, timeout=120):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip()


print("=" * 76)
print("BARIS 1800-1825 Main.js — syarat canBranding")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"sed -n '1800,1825p' {F}\""))

print("\n" + "=" * 76)
print("BARIS 2630-2655 — logika customization.about")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"sed -n '2630,2655p' {F}\""))

print("\n" + "=" * 76)
print("SIAPA yang set asc_setCustomization (dari server OO)")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"grep -rn 'asc_setCustomization' "
         f"/var/www/onlyoffice/documentserver/ --include=*.js 2>/dev/null "
         f"| head -8\""))
