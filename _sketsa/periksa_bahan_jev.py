#!/usr/bin/env python3
"""PERIKSA: apa yang SEBENARNYA dilihat Jev? (05Okt26)

Curiga: Jev hanya menerima cuplikan 400 karakter → tidak melihat penomoran
bertingkat → menjawab "2" untuk semua naskah.
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')
from app import satpam                                    # noqa: E402
from app.state import deteksi_bab_besar, buang_daftar_isi  # noqa: E402

NAMA = 'unhas-disertasi-977b0e0831.txt'
teks = open(f'/app/_naskah_uji_teks/{NAMA}', encoding='utf-8').read()
peta = deteksi_bab_besar(teks)

state = satpam._susun_state(teks, peta)
print('═' * 90)
print('  BAHAN YANG DIKIRIM KE JEV (state)')
print('═' * 90)
print(f'  panjang state : {len(state):,} karakter')
print()
# tampilkan HANYA bagian bahan kedalaman (yang baru)
for baris in state.split('\n'):
    if ('BERTINGKAT' in baris or 'KEDALAMAN' in baris
            or 'BAGIAN BESAR' in baris or 'BAGIAN KECIL' in baris):
        print('  ► ' + baris[:150])
print()
print('─' * 90)
print('  BERAPA BANYAK ISI YANG JEV LIHAT vs PANJANG NASKAH')
print('─' * 90)
print(f'  naskah  : {len(teks):,} kar')
print(f'  peta    : {len(peta)} bagian (tiap bagian dikirim 400 kar awal)')
print(f'  → Jev lihat ≈ {len(peta)*400:,} kar isi '
      f'({100*len(peta)*400/max(1,len(teks)):.1f}% dari naskah)')
print()
print('─' * 90)
print('  BUKTI: apakah penomoran bertingkat ADA di dalam isi naskah?')
print('─' * 90)
import re
bersih = buang_daftar_isi(teks)
pola = re.compile(
    r'^\s*([1-9]|[12]\d)((?:\.\d{1,2}){1,4})\.?\s+([A-Z][^\n]{2,110})$',
    re.MULTILINE)
n4 = []
for m in pola.finditer(bersih):
    nomor = f'{m.group(1)}{m.group(2)}'
    d = len([x for x in nomor.strip('.').split('.') if x])
    if d >= 4:
        n4.append(f'{nomor}  {m.group(3).strip()[:52]}  @{m.start()}')
print(f'  baris 4+ tingkat di ISI naskah: {len(n4)}')
for x in n4[:6]:
    print('    ' + x)
print()
print('  APAKAH posisi itu MASUK peta yang dikirim ke Jev?')
for b in peta:
    print(f'    {b["section_id"]:8} {b["char_count"]:>7,} kar  '
          f'({b["char_count"]*100//max(1,len(teks))}% naskah)')
