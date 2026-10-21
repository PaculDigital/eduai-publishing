"""Verifikasi: apakah `post_process` SEKARANG memecah paragraf panjang?"""
import sys

sys.path.insert(0, '/app')
import buku_umum_pipeline as P            # noqa: E402

teks = open('/tmp/uji_buku_baru/bab1.txt', encoding='utf-8').read()
panjang = [b for b in teks.split('\n') if len(b) > 3000]

print('=== post_process BARU pada paragraf panjang ===')
for b in panjang:
    h = P.post_process(b)
    baris = [x for x in h.split('\n') if x.strip()]
    print(f'  SEBELUM: {len(b.split())} kata / {len(b)} kar')
    print(f'  SESUDAH: {len(baris)} paragraf, '
          f'terpanjang {max(len(x) for x in baris)} kar / '
          f'{max(len(x.split()) for x in baris)} kata')
    print()

print('=== post_process pada SELURUH bab ===')
h = P.post_process(teks)
baris = [x for x in h.split('\n') if x.strip()]
print(f'  baris: {len(baris)}')
print(f'  terpanjang: {max(len(x) for x in baris)} kar / '
      f'{max(len(x.split()) for x in baris)} kata')
print(f'  paragraf wajar @25-40 kata: '
      f"{sum(1 for x in baris if 25 <= len(x.split()) <= 40)}")
print()
salah = []
if max(len(x) for x in baris) > 3000:
    salah.append('masih ada baris >3000 kar')
if len(baris) < 12:
    salah.append(f'hanya {len(baris)} baris (harap >=12)')
print('SALAH:', salah)
