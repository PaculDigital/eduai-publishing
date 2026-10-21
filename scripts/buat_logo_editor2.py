#!/usr/bin/env python3
"""Buat logo HEADER EDITOR: ikon burung + 'EduAi' saja.

Struktur logo-320.png (320x127):
  blok0 (x=6-105)   : ikon burung, y=4-122
  blok1-4 (x=127-305): teks, terbagi 2 baris:
      - baris atas  y=21..~55  = 'INOVASI'   <- BUANG
      - baris bawah y=~57..94  = 'EduAi'     <- SISAKAN

Rencana:
  1. Ikon burung: crop x=6..105, y=4..122
  2. Teks: crop x=127..305, buang baris atas -> sisakan 'EduAi'
  3. Gabung: [ikon burung] + jarak + [EduAi]
  4. Crop rapat

Output: app/static/logo-editor-320.png
"""
from pathlib import Path

from PIL import Image

BASE = Path('/opt/data/services/eduai-publishing')
im = Image.open(BASE / 'app/static/logo-320.png').convert('RGBA')
W, H = im.size
px = im.load()

# ── 1. ikon burung ──
IKON = (6, 4, 106, 123)          # x0,y0,x1,y1
ikon = im.crop(IKON)
print(f"ikon  : {ikon.size}")

# ── 2. teks: cari baris pemisah 'INOVASI' vs 'EduAi' di area x=127..305 ──
TX0, TX1 = 127, 306
profil = []
for y in range(H):
    n = sum(1 for x in range(TX0, TX1) if px[x, y][3] > 30)
    profil.append(n)

# baris yang berisi (di area teks)
aktif = [y for y, n in enumerate(profil) if n > 0]
print(f"teks  : baris aktif y={aktif[0]}..{aktif[-1]}")

# cari gap (baris kosong) di antara
gap = [y for y in range(aktif[0], aktif[-1] + 1) if profil[y] == 0]
rentang = []
if gap:
    m = gap[0]
    s = gap[0]
    for y in gap[1:]:
        if y != s + 1:
            rentang.append((m, s))
            m = y
        s = y
    rentang.append((m, s))
print(f"teks  : gap = {rentang}")

if not rentang:
    # tidak ada gap -> pakai titik tengah
    titik = (aktif[0] + aktif[-1]) // 2
    print(f"  ⚠️ tidak ada gap; pakai titik tengah y={titik}")
    y_mulai_eduai = titik
else:
    # gap pertama memisahkan INOVASI (atas) dan EduAi (bawah)
    y_mulai_eduai = rentang[0][1] + 1

teks = im.crop((TX0, y_mulai_eduai, TX1, aktif[-1] + 1))
bb = teks.getbbox()
if bb:
    teks = teks.crop(bb)
print(f"teks  : 'EduAi' saja -> {teks.size}")

# ── 3. gabung ──
JARAK = 10
tinggi = max(ikon.size[1], teks.size[1])
lebar = ikon.size[0] + JARAK + teks.size[0]
hasil = Image.new('RGBA', (lebar, tinggi), (0, 0, 0, 0))
# ikon: rata tengah vertikal
hasil.paste(ikon, (0, (tinggi - ikon.size[1]) // 2), ikon)
# teks: rata tengah vertikal
hasil.paste(teks, (ikon.size[0] + JARAK, (tinggi - teks.size[1]) // 2), teks)

bb = hasil.getbbox()
if bb:
    hasil = hasil.crop(bb)
print(f"hasil : {hasil.size}")

KELUAR = BASE / 'app/static/logo-editor-320.png'
hasil.save(KELUAR)
print(f"\n✅ {KELUAR}  ({KELUAR.stat().st_size:,} B)")

# versi 96
w96 = 96
h96 = max(1, round(w96 * hasil.size[1] / hasil.size[0]))
hasil.resize((w96, h96), Image.LANCZOS).save(
    BASE / 'app/static/logo-editor-96.png')
print(f"✅ logo-editor-96.png ({w96}x{h96})")

# preview latar hijau (seperti header editor)
prev = Image.new('RGB', (hasil.size[0] + 40, hasil.size[1] + 40), '#1f6f43')
prev.paste(hasil, (20, 20), hasil)
prev.save(BASE / 'shots' / 'logo-editor-preview.png')
print(f"✅ preview: shots/logo-editor-preview.png")
