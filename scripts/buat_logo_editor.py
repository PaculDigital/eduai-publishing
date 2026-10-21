#!/usr/bin/env python3
"""Buat logo HEADER EDITOR: ikon burung + 'EduAi' saja (TANPA 'INOVASI').

Sumber: app/static/logo-320.png (ikon burung + INOVASI di atas + EduAi bawah)

Cara:
  1. Baca gambar
  2. Cari batas baris 'INOVASI' (baris paling atas yang memuat piksel terang)
     dan baris mulai 'EduAi' (gap kosong di antaranya)
  3. Buang bagian 'INOVASI', simpan sisanya (ikon burung + EduAi)
  4. Crop rapat (buang piksel kosong)

Output: app/static/logo-editor-320.png
"""
import sys
from pathlib import Path

from PIL import Image

BASE = Path('/opt/data/services/eduai-publishing')
SUMBER = BASE / 'app/static/logo-320.png'
KELUAR = BASE / 'app/static/logo-editor-320.png'

im = Image.open(SUMBER).convert('RGBA')
W, H = im.size
print(f"sumber: {SUMBER.name}  {W}x{H}")

px = im.load()

# ── 1. hitung "kepadatan" piksel tidak-transparan per baris ──
baris = []
for y in range(H):
    n = 0
    for x in range(W):
        if px[x, y][3] > 30:
            n += 1
    baris.append(n)

# tampilkan profil singkat
aktif = [y for y, n in enumerate(baris) if n > 2]
if not aktif:
    sys.exit("❌ gambar kosong?")
print(f"  baris berisi piksel: {aktif[0]}..{aktif[-1]}")

# ── 2. cari GAP (baris kosong) yang memisahkan blok ──
gap = []
for y in range(aktif[0], aktif[-1] + 1):
    if baris[y] <= 2:
        gap.append(y)

# kelompokkan gap jadi rentang
rentang = []
if gap:
    mulai = gap[0]
    sebelum = gap[0]
    for y in gap[1:]:
        if y != sebelum + 1:
            rentang.append((mulai, sebelum))
            mulai = y
        sebelum = y
    rentang.append((mulai, sebelum))

print(f"  gap kosong ditemukan: {rentang}")

# ── 3. buang blok PALING ATAS (yaitu 'INOVASI') ──
# asumsi: teks 'INOVASI' ada di blok paling atas, lalu gap, lalu 'EduAi'+burung
potong = aktif[0]
if rentang:
    # gap pertama setelah blok paling atas
    awal_gap = rentang[0][0]
    potong = rentang[0][1] + 1
    print(f"  -> memotong baris 0..{potong-1} (blok 'INOVASI' + gap)")
else:
    print("  ⚠️ tidak ada gap — tidak memotong apa pun")

im2 = im.crop((0, potong, W, H))

# ── 4. crop rapat (bbox) ──
bbox = im2.getbbox()
if bbox:
    im2 = im2.crop(bbox)
print(f"  hasil: {im2.size[0]}x{im2.size[1]} (bbox {bbox})")

im2.save(KELUAR)
print(f"\n✅ {KELUAR}  ({KELUAR.stat().st_size:,} B)")

# juga versi 96 utk jaga-jaga
im2.resize((96, max(1, int(96 * im2.size[1] / im2.size[0]))),
           Image.LANCZOS).save(BASE / 'app/static/logo-editor-96.png')
print(f"✅ {BASE / 'app/static/logo-editor-96.png'}")
