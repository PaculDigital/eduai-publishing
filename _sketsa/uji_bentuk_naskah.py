#!/usr/bin/env python3
"""UJI AKHIR: Jev & MESIN pada BERBAGAI BENTUK NASKAH (05Okt26).

Dua pertanyaan Bos:
  1. Apakah Jev presisi membaca BERBAGAI bentuk naskah?
  2. Apakah MESIN sudah bisa seperti Jev?

Cara ukur: bandingkan keduanya pada 18 naskah asli + hitung "bentuk penomoran"
yang benar-benar dipakai tiap naskah, lalu lihat siapa yang menangkapnya.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app import satpam                                       # noqa: E402
from app.ai import _teks_dari_berkas                         # noqa: E402
from app.state import (buang_daftar_isi, deteksi_bab_besar,   # noqa: E402
                       deteksi_subbab, petakan)

KEL1 = Path('/app/_contoh-dokumen/tesis-bos-gdrive')
KEL2 = Path('/app/_contoh-dokumen')
berkas = sorted(KEL1.glob('*.pdf'))
berkas += sorted(KEL2.glob('*/*.docx'))
berkas += sorted(KEL2.glob('*/*.txt'))

# "kenyataan" = jumlah sub-bab yang BENAR-BENAR ada (dihitung longgar:
#  x.y + A. + 1) supaya tahu berapa yang seharusnya tertangkap)
_P_XY = re.compile(r'^\s*([1-9]|[12]\d)\.\d{1,2}\.?\s+[A-Z]', re.MULTILINE)
_P_AB = re.compile(r'^[ \t]*[A-Z]\.[ \t]+[A-Z][^\n]{3,70}[ \t\r]*$', re.MULTILINE)

print('═' * 104)
print('  BENTUK PENOMORAN NYATA per naskah + apa yang MESIN & JEV tangkap')
print('═' * 104)
print(f'  {"berkas":26} {"x.y":>4} {"A.":>4} {"1)":>4} | {"MESIN BAB":>9} '
      f'{"MESIN sub":>9} | {"JEV bab":>7} {"JEV kedalaman":>12}')
print('─' * 104)

stat = {'xy': 0, 'ab': 0, 'n1': 0, 'bab_ok': 0, 'n': 0}
for p in berkas:
    try:
        t = _teks_dari_berkas(p, p.name)
    except Exception:                                          # noqa: BLE001
        continue
    if not t.strip():
        continue
    bersih = buang_daftar_isi(t)
    n_xy = len(_P_XY.findall(bersih))
    n_ab = len(_P_AB.findall(bersih))
    n_1 = len(re.findall(r'^\s*\d{1,2}\)\s+[A-Z]', bersih, re.MULTILINE))

    bab = deteksi_bab_besar(t)
    sub = deteksi_subbab(t)
    h = satpam.periksa(t, petakan(t))

    stat['xy'] += n_xy
    stat['ab'] += n_ab
    stat['n1'] += n_1
    stat['n'] += 1
    if h.get('jumlah_bab') == len(bab):
        stat['bab_ok'] += 1

    print(f'  {p.name[:26]:26} {n_xy:>4} {n_ab:>4} {n_1:>4} | '
          f'{len(bab):>9} {len(sub):>9} | '
          f'{str(h.get("jumlah_bab")):>7} {str(h.get("kedalaman_subbab")):>12}')

print('─' * 104)
print(f'  naskah            : {stat["n"]}')
print(f'  pakai bentuk x.y  : {stat["xy"]} baris')
print(f'  pakai bentuk A.   : {stat["ab"]} baris')
print(f'  pakai bentuk 1)   : {stat["n1"]} baris')
print(f'  Jev cocok jumlah bab: {stat["bab_ok"]}/{stat["n"]}')
print('═' * 104)
