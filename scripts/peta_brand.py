#!/usr/bin/env python3
"""PEMETAAN JEJAK "OnlyOffice" — cari SEMUA tempat yang perlu di-rebranding.

Diperiksa:
  A. Kode aplikasi kita (eduai-app): konfigurasi customization yang dikirim
     ke editor (logo, about, help, judul, dsb)
  B. File gambar di dalam container oo-converter: logo, favicon, ikon
  C. Teks "OnlyOffice" di berkas locale/bahasa editor
  D. Berkas HTML halaman (welcome/index/example) yang mungkin masih ada
"""
import re
import subprocess

C = 'oo-converter'


def sh(cmd, timeout=120):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip()


print("=" * 78)
print("PEMETAAN JEJAK 'OnlyOffice' — SIAP REBRANDING")
print("=" * 78)

# ── A. KONFIG APLIKASI KITA ────────────────────────────────────────
print("\n" + "─" * 78)
print("A. KONFIGURASI APLIKASI KITA (yang dikirim ke editor)")
print("─" * 78)
out = sh("cd /opt/data/services/eduai-publishing && "
         "grep -n 'logo\\|about\\|help\\|feedback\\|customization\\|title\\|"
         "customer\\|customer_id\\|text\\|hideRightMenu\\|compactHeader' "
         "app/onlyoffice.py | head -40")
print(out or "(tidak ada)")

print("\n── apakah ada config customization lengkap? ──")
out = sh("cd /opt/data/services/eduai-publishing && "
         "sed -n '1,200p' app/onlyoffice.py | grep -n 'customization' ")
print(out or "(tidak ketemu blok customization)")

# ── B. GAMBAR LOGO DI CONTAINER OO ─────────────────────────────────
print("\n" + "─" * 78)
print("B. BERKAS GAMBAR (logo/favicon) di dalam oo-converter")
print("─" * 78)
for pola in ['logo*', 'favicon*', '*onlyoffice*']:
    out = sh(f"docker exec {C} sh -c \"find /var/www/onlyoffice/documentserver "
             f"-iname '{pola}' -type f 2>/dev/null | head -25\"")
    print(f"\n  pola '{pola}':")
    for baris in (out.split('\n') if out else ['(tidak ada)']):
        print(f"    {baris}")
