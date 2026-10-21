#!/usr/bin/env python3
"""TAHAP 1d' — Header BIRU OnlyOffice: ikon burung + 'EduAi' saja.

PERBAIKAN dari kegagalan sebelumnya:
  - SVG lama 150x20 -> kontainer hanya 122x28 -> TERPOTONG jadi 'Edu... IN'
  - Sekarang: SVG dibuat PAS 122x28 (ukuran kotak #header-logo)

Sumber: app/static/logo-editor-320.png (ikon burung + 'EduAi', tanpa INOVASI)
Rasio 289:119 = 2.43:1  ->  122x50? terlalu tinggi.
  Kontainer 122x28 -> tinggi 28, lebar = 28*2.43 = 68 -> pakai 68x28.
  Atau lebar 122, tinggi = 122/2.43 = 50 (terlalu tinggi, akan di-scale CSS).
  CSS: max-width:300px; max-height:20px  -> JADI MAKS 20px TINGGI!
  -> tinggi efektif 20px, lebar = 20*2.43 = 49px.

Jadi SVG cukup 49x20 -> CSS akan render max-height 20px. Itu sebabnya
tampilan sebelumnya 122x28 -> CSS max-height:20px memaksa tinggi 20,
lebar jadi 122 (karena max-width 300) -> GEPENG.

SOLUSI: set SVG width=49 height=20, dan CSS OO akan pakai itu.
"""
import base64
from pathlib import Path

from PIL import Image

BASE = Path('/opt/data/services/eduai-publishing')
PNG = BASE / 'app/static/logo-editor-320.png'

w0, h0 = Image.open(PNG).size
rasio = w0 / h0

# CSS OO: max-width:300px; max-height:20px  -> tinggi jadi 20
H = 20
W = round(H * rasio)
print(f"sumber {w0}x{h0} rasio {rasio:.3f} -> SVG {W}x{H}")

b64 = base64.b64encode(PNG.read_bytes()).decode()
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
       f'viewBox="0 0 {W} {H}" fill="none">'
       f'<image x="0" y="0" width="{W}" height="{H}" '
       f'preserveAspectRatio="xMidYMid meet" '
       f'href="data:image/png;base64,{b64}"/></svg>')

f = BASE / 'brand-ikon' / 'logo-biru-eduai.svg'
f.write_text(svg)
print(f"✅ {f} ({f.stat().st_size:,} B)")

# preview di latar biru OO (#2b3a4a)
prev = Image.new('RGB', (W + 40, H + 40), '#2b3a4a')
im = Image.open(PNG).convert('RGBA').resize((W, H), Image.LANCZOS)
prev.paste(im, (20, 20), im)
prev.save(BASE / 'shots' / 'logo-biru-preview.png')
print(f"✅ preview: shots/logo-biru-preview.png")
