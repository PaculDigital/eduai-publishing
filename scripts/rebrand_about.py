#!/usr/bin/env python3
"""TAHAP 2 REBRANDING — Ganti data About OnlyOffice jadi identitas EduAi INOVASI.

CARA KERJA:
  Community Edition (CE) tidak mengizinkan `customization.customer` dari config
  (terbukti: `canBranding = params.asc_getCustomization()` = false).
  Maka nilai DEFAULT di About.js harus diganti langsung.

  File: web-apps/apps/common/main/lib/view/About.js
  Baris ~172: publishername: 'Ascensio System SIA'  -> 'EduAi INOVASI'
  Plus alamat, mail, telp, www.

  ⚠️ JEBAKAN .gz: nginx OO pakai gzip_static -> yang dikirim file .gz!
     Wajib ganti .js DAN .js.gz.

AMAN: backup dulu ke _arsip/, simpan salinan asli untuk rollback.
"""
import base64
import gzip
import re
import shutil
import subprocess
import sys
from pathlib import Path

C = 'oo-converter'
DS = '/var/www/onlyoffice/documentserver'
F = f'{DS}/web-apps/apps/common/main/lib/view/About.js'

ARSIP = Path('/opt/data/services/eduai-publishing/_arsip')

# data baru
BARU = {
    'publishername': 'EduAi INOVASI',
    'publisheraddr': 'Jl. Raya Bekasi KM 32 - Bekasi',
    'publishermail': 'eduai@bikinaja.id',
    'publisherphone': '+6281-000-000',
    'publisherurl': 'http://eduai.bikinaja.id/',
}


def sh(cmd, timeout=180, binary=False):
    r = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout)
    if binary:
        return r.returncode, r.stdout
    return r.returncode, r.stdout.decode('utf-8', 'replace').strip()


def baca_b64(path):
    """Ambil berkas dari container via base64 (aman untuk biner)."""
    kode, out = sh(f"docker exec {C} sh -c \"base64 -w0 '{path}'\"")
    if kode != 0 or not out:
        return None
    return base64.b64decode(out)


def tulis_b64(path, data: bytes):
    b64 = base64.b64encode(data).decode()
    kode, out = sh(f"docker exec -i {C} sh -c "
                   f"\"base64 -d > '{path}'\"", binary=True) if False else (None, None)
    # tulis via python di dalam container (paling aman)
    kode, out = sh(f"docker exec {C} python3 -c \""
                   f"import base64,sys;"
                   f"open('{path}','wb').write(base64.b64decode(sys.argv[1]))\" "
                   f"'{b64}'")
    return kode == 0


print("=" * 76)
print("TAHAP 2 — REBRANDING ABOUT (ganti data default OO)")
print("=" * 76)

# ── 1. BACKUP ──────────────────────────────────────────────────────
print("\n[1] BACKUP file About.js dari container")
isi_asli = baca_b64(F)
if isi_asli is None:
    print("❌ gagal baca About.js")
    sys.exit(1)
print(f"    ukuran asli: {len(isi_asli):,} B")

gz_asli = baca_b64(F + '.gz')
print(f"    ukuran .gz : {len(gz_asli):,} B" if gz_asli else "    (.gz tidak ada)")

simpan = ARSIP / 'oo-about-asli'
simpan.mkdir(parents=True, exist_ok=True)
(simpan / 'About.js').write_bytes(isi_asli)
if gz_asli:
    (simpan / 'About.js.gz').write_bytes(gz_asli)
print(f"    ✅ backup: {simpan}")

# ── 2. CARI nilai default sekarang ─────────────────────────────────
print("\n[2] Nilai default SEKARANG")
teks = isi_asli.decode('utf-8', 'replace')
for kunci in BARU:
    m = re.search(rf"{kunci}\s*:\s*'([^']*)'", teks)
    print(f"    {kunci:16s} = {m.group(1) if m else '(tidak ditemukan)'}")

# ── 3. GANTI ───────────────────────────────────────────────────────
print("\n[3] GANTI nilai")
baru_teks = teks
ganti = 0
for kunci, nilai in BARU.items():
    pola = re.compile(rf"({kunci}\s*:\s*')([^']*)(')")
    baru_teks, n = pola.subn(rf"\g<1>{nilai}\g<3>", baru_teks)
    print(f"    {kunci:16s} -> {nilai}  ({n} penggantian)")
    ganti += n

if ganti == 0:
    print("❌ tidak ada yang diganti — pola tidak cocok")
    sys.exit(1)

data_baru = baru_teks.encode('utf-8')
print(f"    ukuran baru: {len(data_baru):,} B (asli {len(isi_asli):,} B)")

# ── 4. TULIS .js ───────────────────────────────────────────────────
print("\n[4] Tulis About.js")
if tulis_b64(F, data_baru):
    print("    ✅ About.js ditulis")
else:
    print("    ❌ gagal tulis About.js")
    sys.exit(1)

# ── 5. TULIS .gz (WAJIB — nginx kirim yang ini!) ───────────────────
if gz_asli:
    print("\n[5] Tulis About.js.gz (nginx pakai gzip_static)")
    gz_baru = gzip.compress(data_baru, compresslevel=9, mtime=0)
    if tulis_b64(F + '.gz', gz_baru):
        print(f"    ✅ .gz ditulis ({len(gz_baru):,} B)")
    else:
        print("    ❌ gagal tulis .gz")
else:
    print("\n[5] (.gz tidak ada, dilewati)")

# ── 6. VERIFIKASI ──────────────────────────────────────────────────
print("\n[6] VERIFIKASI di container")
kode, out = sh(f"docker exec {C} sh -c \"grep -oE "
               f"\\\"(publishername|publisheraddr|publishermail|publisherphone|"
               f"publisherurl)\\\\s*:\\\\s*'[^']*'\\\" '{F}' | head -8\"")
print(out or "(kosong)")

print("\n    --- cek .gz benar-benar memuat data baru ---")
kode, out = sh(f"docker exec {C} python3 -c \"import gzip;"
               f"d=gzip.open('{F}.gz','rt',errors='replace').read();"
               f"import re;"
               f"print([m for m in re.findall(r\\\"publishername\\s*:\s*'([^']*)'\\\", d)])\"")
print(f"    {out}")
