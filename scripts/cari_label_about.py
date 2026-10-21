#!/usr/bin/env python3
"""Cari SUMBER label 'surel'/'email' & 'www.' di About OO."""
import subprocess

OO = 'oo-converter'
DS = '/var/www/onlyoffice/documentserver'
ABOUT = f'{DS}/web-apps/apps/common/main/lib/view/About.js'


def sh(cmd, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip()


print("=" * 76)
print("1. Label baris di About.js (template) — cari 'surel'/'email'")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"grep -n 'Masuk\\|surel\\|email\\|mail\\|"
         f"telepon\\|tel' {ABOUT} | head -20\""))

print("\n" + "=" * 76)
print("2. Cari di file locale ID (id.json / id-ID.json)")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"ls {DS}/web-apps/apps/common/main/"
         f"resources/ | grep -i '^id' | head -5\""))
print(sh(f"docker exec {OO} sh -c \"find {DS} -name 'id*.json' -path "
         f"'*locale*' 2>/dev/null | head -5\""))
print(sh(f"docker exec {OO} sh -c \"find {DS} -name 'id*.json' 2>/dev/null "
         f"| head -8\""))

print("\n" + "=" * 76)
print("3. Cari kata 'surel' di SELURUH web-apps (kode yg dipakai About)")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"grep -rln 'surel' {DS}/web-apps/ "
         f"2>/dev/null | head -8\""))

print("\n" + "=" * 76)
print("4. Cari kata 'surel' di SELURUH documentserver")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"grep -rln 'surel' {DS}/ 2>/dev/null "
         f"| head -10\""))

print("\n" + "=" * 76)
print("5. 'www.' muncul dari mana? cek fungsi yg menambah www")
print("=" * 76)
print(sh(f"docker exec {OO} sh -c \"grep -rn 'www\\.' {ABOUT} | head -8\""))
