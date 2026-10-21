#!/usr/bin/env python3
"""TAHAP 1d: cari SUMBER tulisan 'ONLYOFFICE' di bar atas editor.

Kandidat:
  - appHeader setBranding() -> pakai config kita (kita set logo:visible False)
  - gambar/svg logo OO di resources
  - teks branding dari api.js
Juga cari judul 'ONLYOFFICE Document Editor' (1b).
"""
import subprocess

OO = 'oo-converter'
DS = '/var/www/onlyoffice/documentserver'


def sh(cmd, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip()


print("=" * 76)
print("1. FILE main/index.html — <title> (1b)")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"grep -rn '<title>' "
         f"{DS}/web-apps/apps/*/main/index.html "
         f"{DS}/web-apps/apps/*/embed/index.html "
         f"{DS}/web-apps/apps/*/forms/index.html 2>/dev/null\""))

print("\n" + "=" * 76)
print("2. Dari mana header editor mengambil logo/branding? (setBranding)")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"grep -rn 'setBranding' "
         f"{DS}/web-apps/ --include=*.js 2>/dev/null | head -8\""))

print("\n" + "=" * 76)
print("3. Berkas logo/header di resources (yg tampil di bar biru)")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"find {DS}/web-apps/apps/common/main/"
         f"resources -maxdepth 2 -name '*logo*' -o -maxdepth 2 -name '*header*' "
         f"2>/dev/null | head -20\""))

print("\n" + "=" * 76)
print("4. Cari teks 'ONLYOFFICE' di main/resources (yg mungkin tampil)")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"grep -rl 'ONLYOFFICE' "
         f"{DS}/web-apps/apps/common/main/resources/ 2>/dev/null | head -10\""))

print("\n" + "=" * 76)
print("5. Cari berkas SVG/PNG logo di seluruh web-apps")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"find {DS}/web-apps -iname '*logo*.svg' "
         f"-o -iname '*logo*.png' 2>/dev/null | head -25\""))
