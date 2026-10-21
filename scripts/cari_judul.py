#!/usr/bin/env python3
"""Cari SEMUA <title> di dalam OO + semua teks 'EduAi Publishing' di kode kita."""
import subprocess

C = 'oo-converter'
DS = '/var/www/onlyoffice/documentserver'


def sh(cmd, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout.strip()


print("=" * 78)
print("A. SEMUA <title> DI DALAM HTML OO (yang bisa tampil di tab/iframe)")
print("=" * 78)
out = sh(f"docker exec {C} sh -c \"grep -rl '<title>' {DS}/web-apps/apps "
         f"--include=*.html 2>/dev/null | head -30\"")
berkas = [b for b in out.split('\n') if b.strip()]
print(f"  jumlah berkas .html ber-<title>: {len(berkas)}")
for b in berkas[:25]:
    t = sh(f"docker exec {C} sh -c \"grep -o '<title>[^<]*</title>' '{b}' "
           f"2>/dev/null | head -1\"")
    if t:
        print(f"    {t[:60]:42s} <- {b.replace(DS, '')}")

print("\n" + "=" * 78)
print("B. INDEX UTAMA EDITOR (yang jadi judul iframe)")
print("=" * 78)
for ed in ['documenteditor', 'spreadsheeteditor', 'presentationeditor',
           'pdfeditor', 'visioeditor']:
    f = f'{DS}/web-apps/apps/{ed}/main/index_loader.html'
    t = sh(f"docker exec {C} sh -c \"grep -o '<title>[^<]*</title>' '{f}' "
           f"2>/dev/null\"")
    print(f"  {ed:22s}: {t or '(tidak ada index_loader)'}")

print("\n" + "=" * 78)
print("C. TEKS 'EduAi PUBLISHING' DI KODE KITA (harus jadi 'EduAi INOVASI')")
print("=" * 78)
out = sh("cd /opt/data/services/eduai-publishing && grep -rn 'EduAi Publishing' "
         "app/ web/ --include=*.py --include=*.html --include=*.js "
         "--include=*.css 2>/dev/null | head -25")
print(out or '(tidak ada)')

print("\n" + "=" * 78)
print("D. 'ONLYOFFICE' / 'OnlyOffice' DI KODE KITA")
print("=" * 78)
out = sh("cd /opt/data/services/eduai-publishing && grep -rn 'OnlyOffice\\|"
         "ONLYOFFICE' app/ web/ --include=*.py --include=*.html --include=*.js "
         "2>/dev/null | grep -v 'onlyoffice.py:' | head -15")
print(out or '(tidak ada)')
