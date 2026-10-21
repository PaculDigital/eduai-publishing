#!/usr/bin/env python3
"""Analisa PROFIL BARIS logo-320.png untuk temukan batas 'INOVASI' vs 'EduAi'."""
from pathlib import Path

from PIL import Image

BASE = Path('/opt/data/services/eduai-publishing')
im = Image.open(BASE / 'app/static/logo-320.png').convert('RGBA')
W, H = im.size
px = im.load()

print(f"ukuran: {W}x{H}\n")
print("y  : jumlah piksel  : bar chart")
for y in range(H):
    n = sum(1 for x in range(W) if px[x, y][3] > 30)
    if n:
        print(f"{y:3d}: {n:4d}  {'#' * min(60, n // 4)}")
