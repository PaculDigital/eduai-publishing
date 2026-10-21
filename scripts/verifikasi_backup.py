#!/usr/bin/env python3
"""VERIFIKASI BACKUP BENAR-BENAR BISA DIPULIHKAN (bukan cuma 'file ada').

Yang diuji:
  1. image tar.gz bisa dibaca & memuat manifest yang benar
  2. tag cadangan ada di docker
  3. DB backup bisa dibuka & isinya cocok live
  4. kode tar.gz bisa dibaca & memuat file penting
"""
import json
import subprocess
import tarfile
import sqlite3
import gzip
from pathlib import Path

DIR = Path('/opt/data/services/eduai-publishing/_arsip/pre-cachecf-20260912-095415')


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


print("=" * 74)
print("VERIFIKASI BACKUP — APAKAH BENAR-BENAR BISA DIPULIHKAN?")
print("=" * 74)

# 1. IMAGE
print("\n── 1. IMAGE tar.gz")
f = DIR / 'image-v1-gzip.tar.gz'
print(f"   ada     : {f.exists()} ({f.stat().st_size/1e6:.1f} MB)")
try:
    with gzip.open(f, 'rb') as gz:
        tf = tarfile.open(fileobj=gz, mode='r|')
        nama = []
        for m in tf:
            nama.append(m.name)
            if len(nama) > 8:
                break
    print(f"   dibaca  : ✅ tar valid, awal: {nama[:3]}")
    idx = 'manifest.json' in ' '.join(nama) or any('manifest' in n for n in nama)
    print(f"   manifest: {'✅ ada' if idx else '⚠️ belum terlihat di 8 entri awal'}")
except Exception as e:
    print(f"   ❌ GAGAL dibaca: {e}")

# 2. TAG CADANGAN
print("\n── 2. TAG CADANGAN di Docker")
kode, out, _ = sh("docker images eduai-app:cadangan-pra-cachecf --format '{{.Tag}} {{.Size}} {{.ID}}'")
print(f"   {out if out else '❌ TIDAK ADA'}")

# 3. DB
print("\n── 3. DB backup")
dbf = DIR / 'eduai.db'
try:
    c = sqlite3.connect(f'file:{dbf}?mode=ro', uri=True)
    integ = c.execute('PRAGMA integrity_check').fetchone()[0]
    ntr = c.execute('SELECT COUNT(*) FROM transaksi').fetchone()[0]
    nus = c.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    nfl = c.execute('SELECT COUNT(*) FROM files').fetchone()[0]
    c.close()
    print(f"   integritas : {integ}")
    print(f"   transaksi  : {ntr} | users: {nus} | files: {nfl}")
except Exception as e:
    print(f"   ❌ GAGAL: {e}")

# 4. KODE
print("\n── 4. KODE tar.gz")
kf = DIR / 'kode-app.tar.gz'
try:
    with tarfile.open(kf, 'r:gz') as tf:
        isi = tf.getnames()
    penting = ['app/main.py', 'app/models.py', 'Dockerfile', 'requirements.txt']
    print(f"   total entri: {len(isi)}")
    for p in penting:
        ada = any(x.endswith(p) for x in isi)
        print(f"   {p:26s}: {'✅' if ada else '❌ TIDAK ADA'}")
except Exception as e:
    print(f"   ❌ GAGAL: {e}")

# 5. BANDING DB backup vs live
print("\n── 5. BANDING DB backup vs LIVE")
kode, out, _ = sh("""docker exec eduai-app python3 -c "
import sqlite3
c=sqlite3.connect('file:/app/data/eduai.db?mode=ro',uri=True)
print(c.execute('SELECT COUNT(*) FROM transaksi').fetchone()[0])
print(c.execute('SELECT COUNT(*) FROM users').fetchone()[0])
print(c.execute('SELECT COUNT(*) FROM files').fetchone()[0])
c.close()" """)
if kode == 0:
    live = out.split()
    try:
        c = sqlite3.connect(f'file:{dbf}?mode=ro', uri=True)
        bkp = [str(c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0])
               for t in ('transaksi', 'users', 'files')]
        c.close()
        cocok = live == bkp
        print(f"   live  : transaksi={live[0]} users={live[1]} files={live[2]}")
        print(f"   backup: transaksi={bkp[0]} users={bkp[1]} files={bkp[2]}")
        print(f"   {'✅ COCOK' if cocok else '⚠️ BERBEDA (ada perubahan setelah backup?)'}")
    except Exception as e:
        print(f"   gagal banding: {e}")
else:
    print(f"   gagal baca live: {out}")

print("\n" + "=" * 74)
