"""Bedah LANJUTAN translator: baca route.js secara utuh (cari struktur data)."""
import re

for p in ('translate', 'save', 'load'):
    src = open(f'/tmp/9router_cek/translator_{p}.js', encoding='utf-8', errors='replace').read()
    print('=' * 72)
    print(f'translator/{p}.js  ({len(src)} byte)')
    print('=' * 72)
    # cetak potongan awal (biasanya berisi skema)
    print(src[:1800])
    print('   ... [potongan akhir] ...')
    print(src[-900:])
    print()
