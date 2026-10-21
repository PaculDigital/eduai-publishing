#!/usr/bin/env python3
"""PERBAIKAN: header BIRU (OnlyOffice) = ikon burung + 'EduAi' saja.

Bos salah paham sebelumnya:
  - header HIJAU (EduAi) -> Wulan salah ganti (INOVASI dihapus) -> KEMBALIKAN
  - header BIRU (OnlyOffice) -> ini yang Bos maksud -> ganti jadi burung + EduAi

Jadi:
  1. KEMBALIKAN editor.html ke logo-320.png (INOVASI masih ada di header hijau)
  2. Buat SVG baru utk header biru: ikon burung + 'EduAi' (tanpa INOVASI)
  3. Timpa dark-logo_s.svg + header-logo_s.svg (+.gz)
"""
import base64
from pathlib import Path

BASE = Path('/opt/data/services/eduai-publishing')

# logo-editor-320.png = ikon burung + EduAi (sudah dibuat sebelumnya)
GAMBAR = BASE / 'app/static/logo-editor-320.png'
print(f"pakai: {GAMBAR.name}")

PNG_B64 = base64.b64encode(GAMBAR.read_bytes()).decode()

W, H = 150, 24   # rasio 289:119 -> 150:62? terlalu tinggi. pakai 24 tinggi
# rasio asli 289x119 = 2.43:1  ->  58x24
W, H = 58, 24

svg_gelap = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}" fill="none">'
             f'<image x="0" y="0" width="{W}" height="{H}" '
             f'href="data:image/png;base64,{PNG_B64}"/></svg>')

keluar = BASE / 'brand-ikon'
(KELUAR := keluar / 'logo-biru-eduai.svg').write_text(svg_gelap)
print(f"✅ {KELUAR} ({KELUAR.stat().st_size:,} B)")
print(f"   viewBox {W}x{H} (rasio sama dgn logo burung+EduAi)")
