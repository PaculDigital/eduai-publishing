#!/usr/bin/env python3
"""PAKSA logo tampil di dialog About (abaikan canBranding=false).

Cara:
  1. Salin logo ke container OO (di folder img/about)
  2. Suntik CSS ke app.css: .asc-about-office { background-image: url(...) }
     -> div kosong jadi berisi gambar
  3. Ganti .gz juga (jebakan gzip_static)

Backup dulu.
"""
import gzip
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

OO = 'oo-converter'
DS = '/var/www/onlyoffice/documentserver'
CSS = f'{DS}/web-apps/apps/documenteditor/main/resources/css/app.css'
IMG_DIR = f'{DS}/web-apps/apps/common/main/resources/img/header'
BASE = Path('/opt/data/services/eduai-publishing')
LOGO = BASE / 'app/static/logo-about-256.png'
ARSIP = BASE / '_arsip/oo-about-logo'
ARSIP.mkdir(parents=True, exist_ok=True)


def jalan(cmd, cek=True, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout)
    if cek and r.returncode != 0:
        print(f"❌ {cmd[:80]}\n   {r.stderr.decode()[:300]}")
        sys.exit(1)
    return r.stdout


def baca(path):
    return jalan(f'docker exec {OO} cat {path}').decode('utf-8', 'replace')


def tulis(path, data: bytes):
    """Tulis file di container via stdin (aman utk data besar)."""
    import base64
    b64 = base64.b64encode(data).decode()
    kode = (f"import base64,sys;"
            f"open({path!r},'wb').write(base64.b64decode(sys.stdin.buffer.read()))")
    r = subprocess.run(f'docker exec -i {OO} python3 -c {kode!r}',
                       shell=True, input=b64.encode(),
                       capture_output=True, timeout=300)
    if r.returncode != 0:
        print(f"❌ tulis {path}: {r.stderr.decode()[:300]}")
        sys.exit(1)


print("=" * 76)
print("1. BACKUP app.css + .gz")
print("=" * 76)
for f in [CSS, CSS + '.gz']:
    data = jalan(f'docker exec {OO} cat {f}')
    nama = Path(f).name + ('' if not f.endswith('.gz') else '')
    (ARSIP / Path(f).name).write_bytes(data)
    print(f"  {Path(f).name}: {len(data):,} B -> {ARSIP / Path(f).name}")

# ── 2. salin logo ke container ──
print("\n" + "=" * 76)
print("2. SALIN logo ke container OO")
print("=" * 76)
nama_logo = 'logo-about-eduai.png'
tujuan = f'{IMG_DIR}/{nama_logo}'
tulis(tujuan, LOGO.read_bytes())
cek = jalan(f'docker exec {OO} sh -c "ls -la {tujuan}"').decode()
print(f"  {cek.strip()}")

# ── 3. suntik CSS ──
print("\n" + "=" * 76)
print("3. SUNTIK CSS")
print("=" * 76)
css = baca(CSS)
print(f"  app.css sebelum: {len(css):,} B")

PENANDA = '/* EDUAI-BRANDING-ABOUT */'
css_bersih = css
if PENANDA in css_bersih:
    # hapus suntikan lama
    a = css_bersih.find(PENANDA)
    b = css_bersih.find('/* /EDUAI-BRANDING-ABOUT */')
    if b > a:
        css_bersih = css_bersih[:a] + css_bersih[b + len('/* /EDUAI-BRANDING-ABOUT */'):]
    print("  suntikan lama dibersihkan")

# URL relatif dari css -> img/header
suntikan = (
    f'\n{PENANDA}\n'
    f'.asc-about-office{{'
    f'background-image:url("../../../../common/main/resources/img/header/{nama_logo}")!important;'
    f'background-size:contain;background-position:center;'
    f'width:220px;height:170px;margin:0 auto 5px auto;}}\n'
    f'/* /EDUAI-BRANDING-ABOUT */\n')

css_baru = css_bersih + suntikan
tulis(CSS, css_baru.encode('utf-8'))
print(f"  app.css sesudah: {len(css_baru):,} B")

# .gz
gz = gzip.compress(css_baru.encode('utf-8'), 9, mtime=0)
tulis(CSS + '.gz', gz)
print(f"  app.css.gz: {len(gz):,} B")

# ── 4. verifikasi ──
print("\n" + "=" * 76)
print("4. VERIFIKASI")
print("=" * 76)
v = jalan(f'docker exec {OO} sh -c "grep -c EDUAI-BRANDING-ABOUT {CSS}"').decode().strip()
print(f"  penanda di app.css: {v}")
v2 = jalan(f'docker exec {OO} sh -c "grep -c EDUAI-BRANDING-ABOUT {CSS}.gz 2>/dev/null || echo 0"').decode().strip()
print(f"  penanda di .gz (binary grep): {v2}")
v3 = jalan(f'docker exec {OO} sh -c "ls -la {tujuan}"').decode().strip()
print(f"  logo: {v3}")

print("\n✅ SELESAI")
