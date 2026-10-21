"""Gambar WATERMARK MENYATU v4 — posisi teks DIPERBAIKI.

KOREKSI BOS: "tulisan DEMO pratinjau di logo kurang turun di bawah paruh
harusnya" ⇒ DEMO + PRATINJAU harus di BAWAH logo (bukan menumpuk di
paruh/wajah burung).

v5:
  · Logo burung ditaruh di ATAS
  · "DEMO" + "PRATINJAU" ditaruh DI BAWAH logo (di bawah paruh) — tidak
    menumpuk wajah
  · Ukuran 2000x1600 (lebih tinggi, karena logo + teks bertumpuk vertikal)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

KELUAR = Path('/opt/data/services/eduai-publishing/app/static/watermark-uji-mirip.png')
LOGO = Path('/opt/data/services/eduai-publishing/app/static/logo-about-256.png')

W, H = 2000, 1600

kanvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))

#  ── 1. LOGO burung — di ATAS, samar ────────────────────────────────
logo = Image.open(LOGO).convert('RGBA')
bb = logo.getbbox()
if bb:
    logo = logo.crop(bb)

tinggi_logo = int(H * 0.52)
logo = logo.resize((int(tinggi_logo * logo.width / logo.height), tinggi_logo),
                   Image.LANCZOS)
a = logo.split()[3].point(lambda v: int(v * 0.24))
logo.putalpha(a)

logo_x = (W - logo.width) // 2
logo_y = int(H * 0.06)
kanvas.alpha_composite(logo, (logo_x, logo_y))

#  ── 2. Font ────────────────────────────────────────────────────────
KANDIDAT = [
    '/opt/data/.fonts/Carlito-Bold.ttf',
    '/opt/data/.fonts/LiberationSans-Bold.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
]
jalur = next((j for j in KANDIDAT if Path(j).exists()), None)
f_demo = ImageFont.truetype(jalur, 300) if jalur else ImageFont.load_default()
f_prat = ImageFont.truetype(jalur, 92) if jalur else ImageFont.load_default()

g = ImageDraw.Draw(kanvas)

#  ── 3. "DEMO" DI BAWAH LOGO (di bawah paruh) ──────────────────────
y_mulai_teks = logo_y + logo.height + int(H * 0.02)

kb = g.textbbox((0, 0), "DEMO", font=f_demo)
tw = kb[2] - kb[0]
tx = (W - tw) // 2 - kb[0]
ty = y_mulai_teks - kb[1]
g.text((tx, ty), "DEMO", font=f_demo, fill=(186, 32, 24, 60))

#  ── 4. "PRATINJAU" di bawah DEMO ──────────────────────────────────
kb2 = g.textbbox((0, 0), "DEMO", font=f_demo)
tinggi_demo = kb2[3] - kb2[1]
kk = g.textbbox((0, 0), "PRATINJAU", font=f_prat)
kx = (W - (kk[2] - kk[0])) // 2 - kk[0]
g.text((kx, y_mulai_teks + tinggi_demo + 20 - kk[1]), "PRATINJAU",
       font=f_prat, fill=(186, 32, 24, 105))

kanvas.save(KELUAR)

im = Image.open(KELUAR)
px = im.load()
#  cek: apakah ADA piksel teks di area LOGO (artinya masih menumpuk)?
tumpuk = 0
for y in range(logo_y, min(logo_y + logo.height, im.size[1]), 4):
    for x in range(0, im.size[0], 4):
        if px[x, y][3] > 0:
            tumpuk += 1
print(f"  jadi: {im.size[0]}x{im.size[1]} · {KELUAR.stat().st_size} byte")
print(f"  logo di y {logo_y}..{logo_y+logo.height} · teks mulai y {y_mulai_teks}")
print(f"  (info) piksel berisi di area logo: {tumpuk}")
