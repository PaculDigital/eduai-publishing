"""Cari AKAR `IndexError: list index out of range` di jalur `naskah` langsung.

KENAPA: uji C7 skenario N3 (jalur `naskah` langsung, TANPA file_id) →
    `proses_ai id 102` gagal `IndexError: list index out of range`.
    Ini BUG NYATA (bukan 503 jujur). Harus ketemu barisnya.
"""
import asyncio
import os
import sys
import tempfile
import traceback

_t = tempfile.mkdtemp(prefix='c7n_')
os.environ['EDUAI_DATA_DIR'] = _t
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(_t, 'up')
sys.path.insert(0, '/app')

#  Tiru PERSIS yang dikirim uji skenario N: `naskah` 9.000 kar + 1 komentar.
from app import ai as A                                        # noqa: E402

naskah = open('/app/_naskah_uji_c7.txt', encoding='utf-8').read()[:9000]
print(f'naskah = {len(naskah):,} kar')

#  Cari fungsi yang dipakai jalur `naskah` langsung.
for nama in dir(A):
    if 'naskah' in nama.lower() or 'langsung' in nama.lower():
        print(f'  fungsi mencurigakan: {nama}')

print()
print('=== coba potong_cerdas + bagian (lokasi umum IndexError) ===')
try:
    bagian = A.potong_cerdas(naskah)
    print(f'  potong_cerdas → {len(bagian)} bagian, '
          f'panjang: {[len(b) for b in bagian]}')
except Exception:
    print('  ❌ potong_cerdas GAGAL:')
    traceback.print_exc()

print()
print('=== jalankan _panggil_router dengan teks ini (nyata) ===')
try:
    h = asyncio.run(A._panggil_router(naskah, 60))
    print(f'  OK → {str(h[0])[:150]}')
except Exception:
    print('  ❌ GAGAL:')
    traceback.print_exc()
