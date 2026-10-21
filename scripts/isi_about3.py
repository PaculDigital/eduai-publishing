#!/usr/bin/env python3
"""Cari nilai DEFAULT About (publisher name/address/email/url) + appName."""
import subprocess

C = 'oo-converter'
DS = '/var/www/onlyoffice/documentserver'
ABOUT = f'{DS}/web-apps/apps/common/main/lib/view/About.js'


def sh(cmd, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout


print("=" * 78)
print("NILAI DEFAULT ABOUT (yang tampil kalau tidak dikustom)")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"grep -nE 'publishername|publisheraddr|"
         f"publisherurl|supportemail|phonenum|publishertitle|appName' {ABOUT} "
         f"| tail -25\"")
print(out or '(tidak ada)')

print("\n" + "=" * 78)
print("LOGO 'asc-about-office' — dari CSS mana?")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"grep -rn 'asc-about-office' {DS}/web-apps/apps/"
         f"common/main/resources/css/*.css 2>/dev/null | head -5\"")
print(out or '(tidak ada di css common)')
out = sh(f"docker exec {C} sh -c \"grep -rln 'asc-about-office' {DS}/web-apps/ "
         f"2>/dev/null | head -5\"")
print(out or '(tidak ketemu)')

print("\n" + "=" * 78)
print("NILAI DARI SERVER (defaults di config/JSON)")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"grep -rn 'publisher\\|supportemail\\|phonenum' "
         f"{DS}/server/Common/config/ 2>/dev/null | head -10\"")
print(out or '(tidak ada di server config)')

print("\n" + "=" * 78)
print("CEK VERSI & APP NAME")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"grep -rn 'txtVersionNum' {ABOUT}\"")
print(out)
out = sh(f"docker exec {C} sh -c \"grep -rn 'appName' {DS}/web-apps/apps/"
         f"documenteditor/main/app.js 2>/dev/null | head -5\"")
print(out or '(tidak ada di app.js)')
