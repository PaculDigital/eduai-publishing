#!/usr/bin/env python3
"""Olah ikon burung: hilangkan latar HITAM -> transparan, jadikan persegi.

Menghasilkan:
  brand-ikon/ikon-burung-asli.png      (copy asli sebagai arsip)
  brand-ikon/ikon-burung-512.png       (512x512 persegi, transparan)
  brand-ikon/ikon-burung-256.png
  brand-ikon/ikon-burung-128.png
  brand-ikon/ikon-burung-64.png
  brand-ikon/ikon-burung-32.png
  brand-ikon/favicon.ico               (multi-ukuran 16/32/48/64)

Cara hapus latar: piksel yang sangat gelap (mendekati hitam) -> alpha 0.
Ambang dipilih hati-hati supaya TIDAK menghapus Toga marun gelap
(bagian dalam topi) atau pupil mata.
"""
import shutil
from pathlib import Path

from PIL import Image

SRC = Path('/opt/data/cache/images/img_3e781b23fe4e.jpg')
OUT = Path('/opt/data/services/eduai-publishing/brand-ikon')
OUT.mkdir(parents=True, exist_ok=True)

# 1. arsip file asli
shutil.copy2(SRC, OUT / 'ikon-burung-asli.jpg')
print(f"[1] arsip asli  : {SRC.name} -> ikon-burung-asli.jpg")

im = Image.open(SRC).convert('RGBA')
w, h = im.size
print(f"[2] sumber      : {w}x{h} px")

# 2. hapus latar hitam -> transparan
px = im.load()
AMBANG = 38          # piksel dgn R,G,B semua < 38 -> dianggap latar hitam
hilang = 0
for y in range(h):
    for x in range(w):
        r, g, b, a = px[x, y]
        if r < AMBANG and g < AMBANG and b < AMBANG:
            px[x, y] = (r, g, b, 0)
            hilang += 1
total = w * h
print(f"[3] latar hitam : {hilang:,} px dihapus ({hilang/total*100:.1f}%)")

# 3. potong ke isi gambar (buang sisa tepi kosong)
bbox = im.getbbox()
print(f"[4] bbox isi    : {bbox}")
im_crop = im.crop(bbox)
print(f"    ukuran isi  : {im_crop.size}")

# 4. jadikan persegi (tengah, latar transparan)
cw, ch = im_crop.size
sisi = max(cw, ch)
kanvas = Image.new('RGBA', (sisi, sisi), (0, 0, 0, 0))
kanvas.paste(im_crop, ((sisi - cw) // 2, (sisi - ch) // 2), im_crop)
print(f"[5] persegi     : {kanvas.size}")

# 5. simpan berbagai ukuran
for ukuran in (512, 256, 128, 64, 32):
    r = kanvas.resize((ukuran, ukuran), Image.LANCZOS)
    f = OUT / f'ikon-burung-{ukuran}.png'
    r.save(f, 'PNG')
    print(f"    -> {f.name}  ({f.stat().st_size:,} B)")

# 6. favicon.ico multi-ukuran
ico = OUT / 'favicon.ico'
kanvas.save(ico, 'ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
print(f"[6] favicon.ico  ({ico.stat().st_size:,} B)")

print("\nSELESAI. Hasil di:", OUT)
