#!/usr/bin/env python3
"""Baca ISI dialog About OnlyOffice + title & aset terkait (untuk diskusi)."""
import subprocess

C = 'oo-converter'
DS = '/var/www/onlyoffice/documentserver'


def sh(cmd, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip()


print("=" * 78)
print("1. TEMPLATE DIALOG 'ABOUT' — file sumbernya")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"find {DS}/web-apps -iname '*about*' -type f "
         f"2>/dev/null | grep -vE 'images/|help/' | head -20\"")
print(out or '(tidak ada)')

print("\n" + "=" * 78)
print("2. TEKS DI DALAM TEMPLATE ABOUT (yang tampil ke user)")
print("=" * 78)
for f in (out.split('\n') if out else []):
    f = f.strip()
    if not f or f.endswith('.gz'):
        continue
    isi = sh(f"docker exec {C} sh -c \"cat '{f}' 2>/dev/null | head -60\"")
    if not isi:
        continue
    print(f"\n── {f}")
    print("─" * 70)
    for b in isi.split('\n')[:45]:
        print("  " + b)

print("\n" + "=" * 78)
print("3. VARIABEL TEKS ABOUT (locale: textAbout, textVersion, dll)")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"cat {DS}/web-apps/apps/documenteditor/main/"
         f"locale/en.json 2>/dev/null | python3 -c \\\"import json,sys; "
         f"d=json.load(sys.stdin); "
         f"print(json.dumps({{k:v for k,v in d.items() if 'about' in k.lower() "
         f"or 'version' in k.lower() or 'copyright' in k.lower()}}, "
         f"indent=1, ensure_ascii=False))\\\"\"")
print(out or '(tidak ada)')

print("\n" + "=" * 78)
print("4. BERKAS YANG DILIHAT SAAT ABOUT DIBUKA (link/aset)")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"grep -oE 'https?://[a-zA-Z0-9./_-]*(onlyoffice|"
         f"ascensio)[a-zA-Z0-9./_-]*' {DS}/web-apps/apps/documenteditor/main/"
         f"locale/en.json 2>/dev/null | sort -u\"")
print(out or '(tidak ada)')

print("\n" + "=" * 78)
print("5. TRADEMARK/COPYRIGHT DI LOCALE (semua berkas)")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"grep -l 'ONLYOFFICE' {DS}/web-apps/apps/"
         f"documenteditor/main/locale/*.json 2>/dev/null | wc -l\"")
print(f"  jumlah berkas locale yang menyebut ONLYOFFICE: {out}")
out = sh(f"docker exec {C} sh -c \"grep -hoE '\\\"[^\\\"]*ONLYOFFICE[^\\\"]*\\\"' "
         f"{DS}/web-apps/apps/documenteditor/main/locale/en.json 2>/dev/null | head\"")
print(f"  contoh di en.json: {out or '(tidak ada)'}")
