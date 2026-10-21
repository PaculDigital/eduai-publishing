#!/usr/bin/env python3
"""TAHAP 1 REBRANDING: ganti judul tab browser OO -> "EduAi INOVASI - Editor".

Mengganti <title> di:
  - web-apps/apps/api/documents/preload.html       (+ .gz)
  - web-apps/apps/api/documents/cache-scripts.html (+ .gz)

⚠️ JEBAKAN 1: nginx OO pakai `gzip_static on` -> yang DIKIRIM ke browser
   adalah berkas .gz, BUKAN .html. WAJIB ganti KEDUANYA.
⚠️ JEBAKAN 2: JANGAN `cat` berkas .gz lewat shell -> UnicodeDecodeError.
   Ambil & tulis lewat base64.

Script ini IDEMPOTEN — aman dijalankan berulang, dan dipakai juga oleh
skrip perbaikan otomatis kalau container oo-converter dibuat ulang.
"""
import base64
import gzip
import re
import subprocess

C = 'oo-converter'
DS = '/var/www/onlyoffice/documentserver'
BASE = f'{DS}/web-apps/apps/api/documents'

JUDUL_BARU = 'EduAi INOVASI - Editor'
BERKAS = ['preload.html', 'cache-scripts.html']


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True)
    return r.returncode, r.stdout.decode('utf-8', 'replace')


def baca_teks(f):
    kode, out = sh(f"docker exec {C} sh -c \"cat '{f}' 2>/dev/null\"")
    return out


def baca_b64(f):
    kode, out = sh(f"docker exec {C} sh -c \"base64 -w0 '{f}' 2>/dev/null\"")
    if kode != 0 or not out.strip():
        return None
    try:
        return base64.b64decode(out.strip())
    except Exception:
        return None


def tulis_teks(isi, f):
    p = subprocess.run(['docker', 'exec', '-i', C, 'sh', '-c',
                        f"cat > '{f}'"], input=isi.encode(),
                       capture_output=True)
    return p.returncode == 0


def tulis_biner(data, f):
    p = subprocess.run(['docker', 'exec', '-i', C, 'sh', '-c',
                        f"base64 -d > '{f}'"],
                       input=base64.b64encode(data), capture_output=True)
    return p.returncode == 0


def ganti_judul(teks):
    m = re.search(r'<title>(.*?)</title>', teks, re.S)
    lama = m.group(1) if m else '(tidak ada <title>)'
    baru = re.sub(r'<title>.*?</title>', f'<title>{JUDUL_BARU}</title>',
                  teks, count=1, flags=re.S)
    return baru, lama


print("=" * 74)
print(f"TAHAP 1 — GANTI JUDUL TAB  ->  {JUDUL_BARU}")
print("=" * 74)

for nama in BERKAS:
    asli = f'{BASE}/{nama}'
    gz = f'{BASE}/{nama}.gz'
    print(f"\n── {nama}")

    # ── .html ──
    isi = baca_teks(asli)
    if not isi:
        print(f"   ❌ tidak bisa baca {asli}")
    else:
        baru, lama = ganti_judul(isi)
        if baru == isi:
            print(f"   ✅ .html sudah benar")
        else:
            ok = tulis_teks(baru, asli)
            print(f"   {'✅' if ok else '❌'} .html  '{lama}' -> '{JUDUL_BARU}'")

    # ── .gz (yang SEBENARNYA dikirim nginx) ──
    mentah = baca_b64(gz)
    if mentah is None:
        print(f"   ⚠️ .gz tidak ada / tidak terbaca")
        continue
    try:
        teks = gzip.decompress(mentah).decode('utf-8', 'replace')
    except Exception as e:
        print(f"   ⚠️ .gz gagal dekompres: {e}")
        continue
    teks_baru, lama2 = ganti_judul(teks)
    if teks_baru == teks:
        print(f"   ✅ .gz   sudah benar")
    else:
        gz_baru = gzip.compress(teks_baru.encode('utf-8'), 9)
        ok = tulis_biner(gz_baru, gz)
        print(f"   {'✅' if ok else '❌'} .gz    '{lama2}' -> '{JUDUL_BARU}'")

print("\nSELESAI.")
