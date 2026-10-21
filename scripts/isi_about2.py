#!/usr/bin/env python3
"""Lihat isi RENDER dialog About (bagian yang tampil ke user)."""
import subprocess

C = 'oo-converter'
F = ('/var/www/onlyoffice/documentserver/web-apps/apps/common/main/'
     'lib/view/About.js')


def sh(cmd, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout


print("=" * 78)
print("ISI About.js — BAGIAN SETELAH HEADER LISENSI (yang tampil ke user)")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"sed -n '40,200p' {F}\"")
print(out or '(kosong)')

print("\n" + "=" * 78)
print("CARI KATA KUNCI: onlyoffice / ascensio / logo / copyright / version")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"grep -niE 'onlyoffice|ascensio|logo|"
         f"copyright|www\\.|http|version|trademark' {F} | grep -v '^ *\\*' | head -40\"")
print(out or '(tidak ada)')
