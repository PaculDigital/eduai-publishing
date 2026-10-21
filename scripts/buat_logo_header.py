#!/usr/bin/env python3
"""TAHAP 1d — Buat SVG logo header OO baru: ikon burung + "EduAi INOVASI".

Menggantikan: web-apps/apps/common/main/resources/img/header/
  dark-logo_s.svg     (dipakai tema terang)
  header-logo_s.svg   (dipakai tema gelap)

Ukuran SVG asli: 85x20. Kita pakai 150x20 (lebih lebar utk teks).

Ikon burung: dari brand-ikon/ikon-burung-512.png -> embed base64.
Teks: "EduAi INOVASI" pakai font sans-serif (vector via <text>).

Output: brand-ikon/logo-header-eduai.svg  (+ varian putih)
"""
import base64
from pathlib import Path

BASE = Path('/opt/data/services/eduai-publishing')
IKON = BASE / 'brand-ikon' / 'ikon-burung-256.png'

PNG_B64 = base64.b64encode(IKON.read_bytes()).decode()
print(f"ikon: {IKON.name} ({len(PNG_B64):,} char base64)")

W, H = 168, 22  # lebar x tinggi (asli 85x20, kita perlu lebih lebar)

# ── SVG untuk tema TERANG (tulisan gelap) ──
svg_gelap = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none">
<image x="0" y="1" width="20" height="20" href="data:image/png;base64,{PNG_B64}"/>
<text x="25" y="16" font-family="Arial, Helvetica, sans-serif" font-size="14" font-weight="700" fill="#2b2b2b">EduAi</text>
<text x="70" y="16" font-family="Arial, Helvetica, sans-serif" font-size="14" font-weight="400" fill="#2b2b2b">INOVASI</text>
</svg>'''

# ── SVG untuk tema GELAP (tulisan putih) ──
svg_terang = svg_gelap.replace('fill="#2b2b2b"', 'fill="#ffffff"')

keluar = BASE / 'brand-ikon'
(keluar / 'logo-header-eduai-gelap.svg').write_text(svg_gelap)
(keluar / 'logo-header-eduai-terang.svg').write_text(svg_terang)

print(f"\n✅ dibuat:")
print(f"   {keluar / 'logo-header-eduai-gelap.svg'}  ({len(svg_gelap):,} B)")
print(f"   {keluar / 'logo-header-eduai-terang.svg'} ({len(svg_terang):,} B)")
print(f"\n   (viewBox {W}x{H}, ikon 20x20 + teks 'EduAi INOVASI')")
