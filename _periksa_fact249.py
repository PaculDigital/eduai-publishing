"""Periksa CACAT fact 249: konstanta & aritmatika _cuplik_pandai."""
import sys
sys.path.insert(0, '/app')
from app import konversi as K

print('=== KONSTANTA DI CONTAINER ===')
for n in ('_CUPLIK_PENUH', '_CUPLIK_AWAL', '_CUPLIK_TENGAH', '_CUPLIK_AKHIR',
          '_CUPLIK_BESAR', '_CUPLIK_BESAR_MIN'):
    print(f'  {n:20} = {getattr(K, n)}')

print()
print('=== ARITMATIKA — bagian BESAR 13.503 kar ===')
h = K._cuplik_pandai('x' * 13503)
print(f'  panjang hasil   : {len(h):,}')
print('  fact 249 klaim  : awal 3.600 + tengah 2.400 + akhir 2.000')
print('  hitung seharusnya: 1600+4000//2=3600 · 1400+4000//4=2400 ·'
      ' 1000+4000//4=2000 → 8.000 + penanda')
print(f'  → rentang penanda: {(len(h)-8000)}')

print()
print('=== ARITMATIKA — bagian SEDANG 3.000 kar ===')
h2 = K._cuplik_pandai('y' * 3000)
print(f'  panjang hasil   : {len(h2):,}')
print('  hitung seharusnya: 1600+1400+1000 = 4.000 + penanda')

print()
print('=== ARITMATIKA — bagian 2.001 kar (batas) ===')
h3 = K._cuplik_pandai('z' * 2001)
print(f'  panjang hasil   : {len(h3):,}  (harus > 2.001 karena dipandai)')

print()
print('=== ARITMATIKA — bagian 2.000 kar (UTUH?) ===')
h4 = K._cuplik_pandai('z' * 2000)
print(f'  panjang hasil   : {len(h4):,}  (harus = 2.000, utuh)')

print()
print('=== ARITMATIKA — bagian 6.000 tepat (batas besar) ===')
h5 = K._cuplik_pandai('z' * 6000)
print(f'  panjang hasil   : {len(h5):,}')
print('  kode: besar = len > 6000 → 6000 TIDAK besar (sedang)')
print('  sedang: 1600+1400+1000 = 4000 + penanda')
