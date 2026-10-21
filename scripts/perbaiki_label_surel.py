#!/usr/bin/env python3
"""Perbaikan About lanjutan:
  1. Ganti label 'surel:' -> 'email:' (di locale bahasa Indonesia)
  2. PASTIKAN www tidak muncul di URL

File locale yang perlu: SEMUA locale id.json yang dipakai editor
(documenteditor, spreadsheeteditor, presentationeditor, visioeditor,
pdfeditor — main/forms/embed/mobile).
"""
import base64
import gzip
import json
import re
import subprocess
import sys
from pathlib import Path

C = 'oo-converter'
DS = '/var/www/onlyoffice/documentserver'
ARSIP = Path('/opt/data/services/eduai-publishing/_arsip/oo-about-asli')


def sh(cmd, timeout=180):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return r.returncode, r.stdout.strip()


def baca(path):
    kode, out = sh(f"docker exec {C} sh -c \"base64 -w0 '{path}'\"")
    return base64.b64decode(out) if kode == 0 and out else None


def tulis(path, data):
    """Tulis berkas di dalam container lewat STDIN (aman untuk data besar)."""
    kode_prog = ("import base64,sys;"
                 f"open({path!r},'wb').write(base64.b64decode(sys.stdin.read()))")
    # kirim base64 via stdin (hindari 'argument list too long')
    b64 = base64.b64encode(data).decode()
    r = subprocess.run(['docker', 'exec', '-i', C, 'python3', '-c', kode_prog],
                       input=b64.encode(), capture_output=True, timeout=180)
    return r.returncode == 0


print("=" * 76)
print("1. TEMUKAN SEMUA locale id.json yang punya 'surel'")
print("=" * 76)
kode, out = sh(f"docker exec {C} sh -c \"grep -rl 'surel' {DS}/web-apps/ "
               f"--include=id.json 2>/dev/null\"")
berkas = [b for b in out.split('\n') if b.strip()]
print(f"  ditemukan {len(berkas)} berkas:")
for b in berkas:
    print(f"    {b.replace(DS, '')}")

print("\n" + "=" * 76)
print("2. LIHAT konteks 'surel' di salah satu berkas")
print("=" * 76)
if berkas:
    kode, out = sh(f"docker exec {C} sh -c \"grep -o '\\\"[^\\\"]*surel[^\\\"]*\\\"' "
                   f"'{berkas[0]}' | head -5\"")
    print(f"  {out}")

print("\n" + "=" * 76)
print("3. GANTI 'surel' -> 'email' di SEMUA locale id.json")
print("=" * 76)
sukses = 0
for b in berkas:
    isi = baca(b)
    if not isi:
        print(f"    ❌ gagal baca {b}")
        continue

    # backup ASLI (kalau belum ada)
    simpan = ARSIP / 'locale' / b.replace(DS, '').lstrip('/')
    simpan.parent.mkdir(parents=True, exist_ok=True)
    if not simpan.exists():
        simpan.write_bytes(isi)

    teks = isi.decode('utf-8', 'replace')
    # ganti nilai JSON yang memuat 'surel' (case-insensitive) -> 'email'
    baru, n = re.subn(r'(:\s*")[Ss]urel(\s*:?\s*")', r'\1email\2', teks)
    if n == 0:
        # pola lain: "surel: "
        baru, n = re.subn(r'[Ss]urel', 'email', teks)

    if n:
        data = baru.encode()
        ok_js = tulis(b, data)
        gz = b + '.gz'
        ada_gz = baca(gz) is not None
        ok_gz = tulis(gz, gzip.compress(data, 9, mtime=0)) if ada_gz else True
        print(f"    {'✅' if (ok_js and ok_gz) else '❌'} "
              f"{b.replace(DS, '')} ({n} ganti)"
              f"{' +gz' if ada_gz else ''}")
        sukses += 1
    else:
        print(f"    ⏭️  {b.replace(DS, '')} (pola tidak cocok)")

print(f"\n  total diperbaiki: {sukses}/{len(berkas)}")

print("\n" + "=" * 76)
print("4. VERIFIKASI: masih ada 'surel'?")
print("=" * 76)
kode, out = sh(f"docker exec {C} sh -c \"grep -rl 'surel' {DS}/web-apps/ "
               f"--include=id.json 2>/dev/null | wc -l\"")
print(f"  berkas id.json yang masih memuat 'surel': {out}")
