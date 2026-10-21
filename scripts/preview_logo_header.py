#!/usr/bin/env python3
"""Render SVG logo header ke PNG untuk verifikasi visual (pakai CloakBrowser)."""
from pathlib import Path

from cloakbrowser import launch

BASE = Path('/opt/data/services/eduai-publishing/brand-ikon')
SVG = BASE / 'logo-header-eduai-gelap.svg'
OUT_DIR = Path('/opt/data/services/eduai-publishing/shots')

html = f'''<!doctype html><html><body style="margin:0;background:#fff">
<div style="padding:20px;background:#fff">
  <p style="font:12px Arial;margin:0 0 8px">Latar TERANG (tulisan gelap):</p>
  <img src="file://{SVG}" style="height:40px">
</div>
<div style="padding:20px;background:#2b3a4a">
  <p style="font:12px Arial;margin:0 0 8px;color:#fff">Latar GELAP (tulisan putih):</p>
  <img src="file://{BASE / 'logo-header-eduai-terang.svg'}" style="height:40px">
</div>
<div style="padding:20px;background:#1f6f43">
  <p style="font:12px Arial;margin:0 0 8px;color:#fff">Latar HIJAU (header EduAi):</p>
  <img src="file://{BASE / 'logo-header-eduai-terang.svg'}" style="height:40px">
</div>
</body></html>'''

f = Path('/tmp/preview_logo.html')
f.write_text(html)

b = launch(headless=True)
p = b.new_page()
p.set_viewport_size({'width': 420, 'height': 260})
p.goto(f'file://{f}', wait_until='load')
p.wait_for_timeout(1200)
out = OUT_DIR / 'logo-header-preview.png'
p.screenshot(path=str(out), full_page=True)
print(f"📸 {out}")
b.close()
