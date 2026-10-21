#!/usr/bin/env python3
"""TAHAP 1d-REVISI: header BIRU (OnlyOffice) = ikon burung + 'EduAi' saja.

Sumber gambar: app/static/logo-editor-320.png
  = ikon burung + 'EduAi' (SUDAH tanpa INOVASI, dibuat sebelumnya)
Rasio 289x119 (~2.43:1).

SVG target: 85x20 (ukuran asli dark-logo_s.svg / header-logo_s.svg).
Rasio 85:20 = 4.25:1 -> logo kita 2.43:1 harus di-fit:
  tinggi 20 -> lebar = 20 * 2.43 = 48.6 -> pakai 49x20
"""
import base64
from pathlib import Path

BASE = Path('/opt/data/services/eduai-publishing')
PNG = BASE / 'app/static/logo-editor-320.png'

b64 = base64.b64encode(PNG.read_bytes()).decode()

# hitung rasio
from PIL import Image
w0, h0 = Image.open(PNG).size
rasio = w0 / h0
H = 20
W = round(H * rasio)
print(f"sumber {w0}x{h0} (rasio {rasio:.2f}) -> SVG {W}x{H}")

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
       f'viewBox="0 0 {W} {H}" fill="none">'
       f'<image x="0" y="0" width="{W}" height="{H}" '
       f'href="data:image/png;base64,{b64}"/></svg>')

# terang & gelap sama (gambar PNG sudah punya warna sendiri)
for nama in ['logo-biru-eduai.svg']:
    f = BASE / 'brand-ikon' / nama
    f.write_text(svg)
    print(f"✅ {f} ({f.stat().st_size:,} B)  viewBox {W}x{H}")
