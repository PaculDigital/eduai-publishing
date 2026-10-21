"""Petakan alat uji: mana yang AMAN (pakai app.ai) vs RAWAN (9router langsung)."""
import re
from pathlib import Path

AKAR = Path('/opt/data/services/eduai-publishing')
aman, rawan = [], []

for f in sorted(AKAR.glob('*.py')) + sorted(AKAR.glob('_sketsa/*.py')):
    try:
        t = f.read_text(errors='ignore')
    except Exception:
        continue
    if 'chat/completions' not in t:
        continue
    nama = str(f.relative_to(AKAR))
    punya_th = 'enable_thinking' in t
    punya_prod = bool(re.search(r'from app\.ai import|from app import ai', t))
    rawan.append((nama, punya_th, punya_prod))

print(f'{"berkas":<52}{"enable_thinking":>16}{"pakai app.ai":>14}')
print('-' * 84)
for nama, th, prod in rawan:
    print(f'{nama:<52}{("ADA" if th else "TIDAK ⚠️"):>16}'
          f'{("ya" if prod else "tidak"):>14}')
print(f'\nTOTAL: {len(rawan)} berkas memanggil 9router langsung')
print(f'  tanpa enable_thinking: {sum(1 for _, th, _ in rawan if not th)}')
print(f'  di root (gampang dipakai lagi): '
      f'{sum(1 for n, _, _ in rawan if "/" not in n)}')
