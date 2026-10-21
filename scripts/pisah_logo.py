#!/usr/bin/env python3
"""Pisahkan IKON BURUNG (kiri) vs TEKS (kanan) di logo-320.png.

Cari KOLOM kosong (vertical gap) yang memisahkan ikon burung dgn teks.
Lalu lihat teks terdiri dari 2 baris (INOVASI di atas, EduAi di bawah).
"""
from pathlib import Path

from PIL import Image

BASE = Path('/opt/data/services/eduai-publishing')
im = Image.open(BASE / 'app/static/logo-320.png').convert('RGBA')
W, H = im.size
px = im.load()

print(f"ukuran: {W}x{H}")
print("\n=== KOLOM (x) yg KOSONG / berisi ===")
kolom = []
for x in range(W):
    n = sum(1 for y in range(H) if px[x, y][3] > 30)
    kolom.append(n)

# tampilkan blok-blok
blok = []
isi = False
mulai = 0
for x in range(W):
    if kolom[x] > 0 and not isi:
        isi, mulai = True, x
    elif kolom[x] == 0 and isi:
        isi = False
        blok.append((mulai, x - 1))
if isi:
    blok.append((mulai, W - 1))
print(f"blok kolom berisi: {blok}")

print("\n=== IKON BURUNG: analisa tinggi tiap blok ===")
for i, (a, b) in enumerate(blok):
    tinggi = [y for y in range(H) if any(px[x, y][3] > 30 for x in range(a, b + 1))]
    print(f"  blok{i} x={a}-{b} (lebar {b-a+1})  y={tinggi[0]}-{tinggi[-1]}")

# simpan tiap blok untuk dilihat
for i, (a, b) in enumerate(blok):
    sub = im.crop((a, 0, b + 1, H))
    bb = sub.getbbox()
    if bb:
        sub = sub.crop(bb)
    f = BASE / 'brand-ikon' / f'pisah-blok{i}.png'
    sub.save(f)
    print(f"  -> {f.name} {sub.size}")
