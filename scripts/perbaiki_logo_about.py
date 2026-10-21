#!/usr/bin/env python3
"""PERBAIKAN LOGO ABOUT — matikan logo bawaan OnlyOffice + perbesar logo burung.

MASALAH:
  CSS bawaan: .about-dlg .asc-about-office:before {
      content: url('.../img/about/logo_s.svg');   <- LOGO ONLYOFFICE
  }
  Kita sudah set background-image (burung), tapi :before MASIH menggambar
  logo OnlyOffice DI BELAKANG -> tumpang-tindih.

PERBAIKAN:
  1. Matikan :before (content: none !important)
  2. Perbesar logo burung (Bos minta BESAR)
  3. Taruh file di img/about/ (folder yang sama dgn logo_s.svg)

Target CSS (semua editor yg punya .about-dlg):
  documenteditor, spreadsheeteditor, presentationeditor, pdfeditor, visioeditor
"""
import gzip
import subprocess
import sys
from pathlib import Path

OO = 'oo-converter'
DS = '/var/www/onlyoffice/documentserver'
BASE = Path('/opt/data/services/eduai-publishing')
LOGO_SRC = BASE / 'app/static/logo-about-256.png'
ARSIP = BASE / '_arsip/oo-about-logo2'
ARSIP.mkdir(parents=True, exist_ok=True)

EDITORS = ['documenteditor', 'spreadsheeteditor', 'presentationeditor',
           'pdfeditor', 'visioeditor']

PENANDA_MULAI = '/* EDUAI-ABOUT-FIX */'
PENANDA_AKHIR = '/* /EDUAI-ABOUT-FIX */'


def sh(cmd, cek=True, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout)
    if cek and r.returncode != 0:
        print(f"❌ {cmd[:70]}\n   {r.stderr.decode()[:250]}")
        sys.exit(1)
    return r.stdout


def baca(path):
    return sh(f'docker exec {OO} cat {path}').decode('utf-8', 'replace')


def tulis(path, data: bytes):
    import base64
    b64 = base64.b64encode(data).decode()
    kode = ("import base64,sys;"
            "open(%r,'wb').write(base64.b64decode(sys.stdin.buffer.read()))"
            % path)
    r = subprocess.run(f'docker exec -i {OO} python3 -c {kode!r}',
                       shell=True, input=b64.encode(),
                       capture_output=True, timeout=300)
    if r.returncode != 0:
        print(f"❌ tulis {path}: {r.stderr.decode()[:250]}")
        sys.exit(1)


# ── 1. salin logo ke img/about/ (lokasi yg sama dgn logo_s.svg) ──
IMG_ABOUT = f'{DS}/web-apps/apps/common/main/resources/img/about'
print("=" * 74)
print("1. SALIN logo burung ke img/about/")
print("=" * 74)
nama = 'logo-eduai-about.png'
tulis(f'{IMG_ABOUT}/{nama}', LOGO_SRC.read_bytes())
print(f"  {sh(f'docker exec {OO} sh -c \"ls -la {IMG_ABOUT}/{nama}\"').decode().strip()}")

# ── 2. proses tiap editor ──
print("\n" + "=" * 74)
print("2. SUNTIK CSS (matikan :before + perbesar logo)")
print("=" * 74)

# URL relatif dari css/ ke img/about/
URL = '../../../../common/main/resources/img/about/' + nama

css_suntikan = (
    f'\n{PENANDA_MULAI}\n'
    # matikan logo OnlyOffice bawaan
    f'.about-dlg .asc-about-office:before{{content:none!important;display:none!important;height:0!important;}}\n'
    # logo burung kita, BESAR
    f'.about-dlg .asc-about-office{{'
    f'background-image:url("{URL}")!important;'
    f'background-size:contain!important;background-position:center!important;'
    f'background-repeat:no-repeat!important;'
    f'width:260px!important;height:230px!important;'
    f'margin:0 auto 10px auto!important;}}\n'
    f'{PENANDA_AKHIR}\n')

diproses = 0
for ed in EDITORS:
    css = f'{DS}/web-apps/apps/{ed}/main/resources/css/app.css'
    ada = sh(f'docker exec {OO} sh -c "test -f {css} && echo ada || echo tidak"').decode().strip()
    if ada != 'ada':
        print(f"  [{ed}] CSS tidak ada, lewat")
        continue

    isi = baca(css)
    # backup (sekali saja per file)
    bak = ARSIP / f'{ed}-app.css'
    if not bak.exists():
        bak.write_bytes(isi.encode('utf-8'))
        sh(f'docker exec {OO} sh -c "cat {css}.gz > /dev/null 2>&1 && echo ok || echo no"')
        gz_raw = sh(f'docker exec {OO} cat {css}.gz')
        (ARSIP / f'{ed}-app.css.gz').write_bytes(gz_raw)
        print(f"  [{ed}] backup: {len(isi):,} B + gz {len(gz_raw):,} B")

    # buang suntikan lama (kalau ada)
    bersih = isi
    for m, a in [(PENANDA_MULAI, PENANDA_AKHIR), ('/* EDUAI-BRANDING-ABOUT */', '/* /EDUAI-BRANDING-ABOUT */')]:
        while m in bersih:
            i = bersih.find(m)
            j = bersih.find(a)
            if j > i:
                bersih = bersih[:i] + bersih[j + len(a):]
            else:
                bersih = bersih[:i]
                break

    baru = bersih + css_suntikan
    tulis(css, baru.encode('utf-8'))
    tulis(css + '.gz', gzip.compress(baru.encode('utf-8'), 9, mtime=0))
    n = sh(f'docker exec {OO} sh -c "grep -c EDUAI-ABOUT-FIX {css}"').decode().strip()
    print(f"  [{ed}] ✅ dipasang (penanda: {n})")
    diproses += 1

# ── 3. verifikasi ──
print("\n" + "=" * 74)
print("3. VERIFIKASI")
print("=" * 74)
for ed in EDITORS:
    css = f'{DS}/web-apps/apps/{ed}/main/resources/css/app.css'
    r = sh(f'docker exec {OO} sh -c "test -f {css} && grep -c \'content:none\' {css} || echo -"').decode().strip()
    print(f"  [{ed}] content:none = {r}")
print(f"\n  file css diproses: {diproses}/{len(EDITORS)}")
print(f"  logo: {sh(f'docker exec {OO} sh -c \"ls -la {IMG_ABOUT}/{nama}\"').decode().strip()}")
print("\n✅ SELESAI")
