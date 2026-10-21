#!/usr/bin/env python3
"""TAHAP 1d — Timpa logo header OO dgn logo EduAi INOVASI (ikon burung+teks).

Mengganti (di oo-converter):
  resources/img/header/dark-logo_s.svg      (+.gz)
  resources/img/header/header-logo_s.svg    (+.gz)
  resources/img/header/icons.svg           (TIDAK diubah)

Backup dulu ke _arsip/oo-header-asli/
"""
import base64
import gzip
import subprocess
import sys
from pathlib import Path

C = 'oo-converter'
HDR = ('/var/www/onlyoffice/documentserver/web-apps/apps/common/main/'
       'resources/img/header')
ARSIP = Path('/opt/data/services/eduai-publishing/_arsip/oo-header-asli')
BASE = Path('/opt/data/services/eduai-publishing/brand-ikon')


def sh(cmd, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.returncode, r.stdout.strip()


def baca(path):
    kode, out = sh(f"docker exec {C} sh -c \"base64 -w0 '{path}'\"")
    return base64.b64decode(out) if kode == 0 and out else None


def tulis(path, data):
    kode_prog = ("import base64,sys;"
                 f"open({path!r},'wb').write(base64.b64decode(sys.stdin.read()))")
    r = subprocess.run(['docker', 'exec', '-i', C, 'python3', '-c', kode_prog],
                       input=base64.b64encode(data), capture_output=True,
                       timeout=180)
    return r.returncode == 0


# tema terang -> dark-logo_s.svg  (tulisan gelap: #2b2b2b)
# tema gelap  -> header-logo_s.svg (tulisan putih)
PETA = {
    'dark-logo_s.svg': BASE / 'logo-biru-eduai.svg',
    'header-logo_s.svg': BASE / 'logo-biru-eduai.svg',
}

print("=" * 76)
print("TAHAP 1d — Ganti logo header OO (ikon burung + EduAi INOVASI)")
print("=" * 76)

ARSIP.mkdir(parents=True, exist_ok=True)
gagal = 0

for nama, sumber in PETA.items():
    sn = sumber.read_text()
    target = f'{HDR}/{nama}'
    gz_target = target + '.gz'

    print(f"\n[{nama}]")
    # 1. backup asli
    asli = baca(target)
    if asli:
        (ARSIP / nama).write_bytes(asli)
        print(f"  backup: {len(asli):,} B -> {ARSIP / nama}")
    else:
        print("  ⚠️ tidak bisa baca asli")

    asli_gz = baca(gz_target)
    if asli_gz:
        (ARSIP / f'{nama}.gz').write_bytes(asli_gz)

    # 2. tulis yang baru
    data = sn.encode()
    ok = tulis(target, data)
    print(f"  tulis {nama}: {'✅' if ok else '❌'} ({len(data):,} B)")
    if not ok:
        gagal += 1

    # 3. tulis .gz (nginx kirim ini!)
    if asli_gz:
        gz = gzip.compress(data, 9, mtime=0)
        ok_gz = tulis(gz_target, gz)
        print(f"  tulis {nama}.gz: {'✅' if ok_gz else '❌'} ({len(gz):,} B)")
        if not ok_gz:
            gagal += 1
    else:
        print("  (.gz tidak ada)")

print("\n" + "=" * 76)
print("VERIFIKASI — isi file di container")
print("=" * 76)
for nama in PETA:
    kode, out = sh(f"docker exec {C} sh -c \"grep -c 'EduAi' "
                   f"{HDR}/{nama} 2>/dev/null || echo 0\"")
    kode2, out2 = sh(f"docker exec {C} sh -c \"grep -c 'ONLYOFFICE' "
                     f"{HDR}/{nama} 2>/dev/null || echo 0\"")
    print(f"  {nama}: 'EduAi'={out}  'ONLYOFFICE'={out2}")

# isi .gz
kode, out = sh(f"docker exec {C} python3 -c \"import gzip;"
               f"d=gzip.open('{HDR}/header-logo_s.svg.gz','rt').read();"
               f"print('EduAi di .gz:', 'EduAi' in d, '| ONLYOFFICE:', "
               f"'ONLYOFFICE' in d)\"")
print(f"  cek .gz: {out}")

print(f"\n{'✅ SELESAI' if gagal == 0 else f'❌ {gagal} GAGAL'}")
