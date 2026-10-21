#!/usr/bin/env python3
"""PEMETAAN LANJUTAN — teks, favicon, HTML, dan gambar yang tampil ke user."""
import subprocess

C = 'oo-converter'
DS = '/var/www/onlyoffice/documentserver'


def sh(cmd, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip()


print("=" * 78)
print("C. TEKS 'OnlyOffice' YANG TAMPIL KE USER")
print("=" * 78)

# Cari di berkas locale terjemahan (yang paling terlihat user)
out = sh(f"docker exec {C} sh -c \"grep -ril 'onlyoffice' {DS}/web-apps/apps/api "
         f"{DS}/web-apps/apps/documenteditor/main/locale 2>/dev/null | head -10\"")
print("\n  berkas locale/api yang menyebut 'onlyoffice':")
for b in (out.split('\n') if out else ['(tidak ada)']):
    print(f"    {b}")

# Favicon ukuran
print("\n" + "─" * 78)
print("D. FAVICON — ukuran & apakah masih logo OO")
print("─" * 78)
out = sh(f"docker exec {C} sh -c \"ls -l {DS}/web-apps/apps/documenteditor/main/"
         f"resources/img/favicon.ico {DS}/server/welcome/img/favicon.ico 2>/dev/null\"")
print(out)

# File HTML utama yang disajikan
print("\n" + "─" * 78)
print("E. HALAMAN HTML (index editor) — cek title & referensi gambar")
print("─" * 78)
out = sh(f"docker exec {C} sh -c \"find {DS}/web-apps/apps/documenteditor/main -name "
         f"'index*.html' -o -name '*.html' | head -5\"")
print(out)
for f in (out.split('\n') if out else []):
    if not f.strip():
        continue
    isi = sh(f"docker exec {C} sh -c \"head -40 '{f}' | grep -iE "
             f"'title|logo|favicon|onlyoffice|icon' \"")
    print(f"\n  ── {f}")
    print("    " + (isi or '(bersih)').replace('\n', '\n    '))

# Default logo di API (yang dipakai kalau logo visible)
print("\n" + "─" * 78)
print("F. LOGO DEFAULT SDK (dipakai kalau logo.visible=true)")
print("─" * 78)
out = sh(f"docker exec {C} sh -c \"find {DS}/web-apps/apps/api -iname '*logo*' "
         f"-o -iname '*icon*' | head -20\"")
print(out or "(tidak ada)")

# Gambar about (dipakai dialog About)
print("\n" + "─" * 78)
print("G. ASET ABOUT/SPLASH (logo besar + teks versi)")
print("─" * 78)
out = sh(f"docker exec {C} sh -c \"ls {DS}/web-apps/apps/documenteditor/main/"
         f"resources/img/ 2>/dev/null | head -30\"")
print(out or "(tidak ada)")

# Ada file .gz? (gzip_static -> WAJIB ganti keduanya!)
print("\n" + "─" * 78)
print("H. ⚠️ PASANGAN .gz (gzip_static ON -> WAJIB ganti bareng!)")
print("─" * 78)
out = sh(f"docker exec {C} sh -c \"find {DS}/web-apps/apps -iname 'logo*.svg.gz' "
         f"| wc -l; find {DS}/web-apps/apps -iname 'logo*.svg' | wc -l\"")
print(f"  jumlah logo*.svg.gz : {out}")
