#!/usr/bin/env python3
"""Buat logo ABOUT: kepala burung BESAR + tulisan 'EduAi INOVASI'.

Susunan (vertikal, untuk dialog About):
      🦜  <- kepala burung besar
   EduAi INOVASI   <- tulisan

Sumber: app/static/logo-320.png (ikon burung + INOVASI/EduAi)
Tapi kita mau tulisan 'EduAi INOVASI' satu baris.
- Ambil kepala burung dari logo-320.png (blok kiri)
- Tulis 'EduAi INOVASI' pakai PIL (font sistem)

Output: app/static/logo-about-256.png (persegi-ish, latar transparan)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path('/opt/data/services/eduai-publishing')
src = Image.open(BASE / 'app/static/logo-320.png').convert('RGBA')
px = src.load()
W, H = src.size

# ── 1. ambil kepala burung (blok kiri, x=6..105) ──
burung = src.crop((6, 4, 106, 123))
bb = burung.getbbox()
if bb:
    burung = burung.crop(bb)
print(f"kepala burung: {burung.size}")

# ── 2. render tulisan 'EduAi INOVASI' ──
KANVAS_L = 512
TINGGI_BURUNG = 300
teks = 'EduAi INOVASI'

# cari font
kandidat = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
    '/opt/data/services/eduai-publishing/app/static/fonts/Inter-Bold.ttf',
]
font = None
for f in kandidat:
    if Path(f).exists():
        font = ImageFont.truetype(f, 62)
        print(f"font: {f}")
        break
if font is None:
    font = ImageFont.load_default()
    print("font: default (kecil)")

# ukur teks
tmp = Image.new('RGBA', (10, 10))
d = ImageDraw.Draw(tmp)
kotak = d.textbbox((0, 0), teks, font=font)
tw, th = kotak[2] - kotak[0], kotak[3] - kotak[1]
print(f"teks '{teks}': {tw}x{th}")

# ── 3. susun kanvas ──
lebar = max(TINGGI_BURUNG, tw) + 40
tinggi = TINGGI_BURUNG + 30 + th + 30
kanvas = Image.new('RGBA', (lebar, tinggi), (0, 0, 0, 0))

# burung (skala)
bw = round(burung.size[0] * TINGGI_BURUNG / burung.size[1])
burung2 = burung.resize((bw, TINGGI_BURUNG), Image.LANCZOS)
kanvas.paste(burung2, ((lebar - bw) // 2, 0), burung2)

# tulisan (putih, di bawah burung)
d2 = ImageDraw.Draw(kanvas)
d2.text(((lebar - tw) // 2 - kotak[0], TINGGI_BURUNG + 30 - kotak[1]),
        teks, font=font, fill=(15, 92, 56, 255))

bb2 = kanvas.getbbox()
if bb2:
    kanvas = kanvas.crop(bb2)
print(f"kanvas: {kanvas.size}")

KELUAR = BASE / 'app/static/logo-about-256.png'
kanvas.save(KELUAR)
print(f"✅ {KELUAR} ({KELUAR.stat().st_size:,} B)")

# preview di latar putih (seperti dialog About)
prev = Image.new('RGB', (kanvas.size[0] + 40, kanvas.size[1] + 40), '#f5f5f5')
prev.paste(kanvas, (20, 20), kanvas)
prev.save(BASE / 'shots' / 'logo-about-preview.png')
print(f"✅ preview: shots/logo-about-preview.png")
