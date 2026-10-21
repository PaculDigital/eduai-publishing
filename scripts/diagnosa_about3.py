#!/usr/bin/env python3
"""Cari DARI MANA About.js mengambil `data.customer` (sumber sebenarnya)."""
import subprocess

OO = 'oo-converter'
DS = '/var/www/onlyoffice/documentserver'
ABOUT = f'{DS}/web-apps/apps/common/main/lib/view/About.js'


def sh(cmd, timeout=120):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip()


print("=" * 76)
print("BAGIAN About.js yang MEMBACA data (konteks lengkap)")
print("=" * 76)
out = sh(f"docker exec {OO} sh -c \"sed -n '195,265p' {ABOUT}\"")
print(out)

print("\n" + "=" * 76)
print("CARI: siapa yang memanggil dengan 'data' (parameter setCustomerInfo?)")
print("=" * 76)
out = sh(f"docker exec {OO} sh -c \"grep -n 'setCustomerInfo\\|customerInfo\\|"
         f"data\\.customer\\|function *(' {ABOUT} | head -20\"")
print(out or '(tidak ada)')

print("\n" + "=" * 76)
print("SIAPA YANG MEMANGGIL fungsi About dgn data customer?")
print("=" * 76)
out = sh(f"docker exec {OO} sh -c \"grep -rn 'setCustomerInfo\\|customer' "
         f"{DS}/web-apps/apps/documenteditor/main/app.js "
         f"{DS}/web-apps/apps/common/main/lib/controller/*.js 2>/dev/null "
         f"| grep -iv 'loaderName' | head -15\"")
print(out or '(tidak ada)')

print("\n" + "=" * 76)
print("Cari 'CustomerInfo' / 'customer' di SELURUH web-apps (siapa mengisi)")
print("=" * 76)
out = sh(f"docker exec {OO} sh -c \"grep -rn 'setCustomerInfo\\|CustomerInfo' "
         f"{DS}/web-apps/ --include=*.js 2>/dev/null | head -15\"")
print(out or '(tidak ada)')
