#!/usr/bin/env python3
"""UKUR KEDALAMAN peta halus pada 97 NASKAH NYATA (05Okt26).

Bedanya dengan ukur putaran-1: naskah ini NASKAH ASLI dari repository kampus
(unhas/unj/uin-suska/walisongo), sudah dibuang duplikat ISI-nya (MD5).

YANG DIUKUR PER NASKAH:
  · jumlah sub-bab 2 tingkat (2.3)      → pola LAMA (produksi sekarang)
  · jumlah sub-sub bab 3 tingkat (2.3.1) → pola BARU
  · jumlah 4+ tingkat (2.3.1.1)          → pola BARU
  · ada/tidak pola lain: BAB romawi, angka Arab, huruf

PENTING: PDF dibaca pakai PyMuPDF di HOST (venv /opt/data/.venv), karena
container produksi TIDAK punya PyMuPDF & memang tidak boleh ditambah.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PETA = Path('/opt/data/services/eduai-publishing/_contoh-dokumen/uji-kedalaman')

#  pola LAMA (persis dari app/state.py:_POLA_SUBBAB)
POLA_LAMA = re.compile(r'^\s*([1-9]|[12]\d)\.(\d{1,2})\.?\s+([A-Z][^\n]{2,110})$',
                       re.MULTILINE)
#  pola BARU: kedalaman berapa pun (2.3 / 2.3.1 / 2.3.1.1 ...)
POLA_BARU = re.compile(
    r'^\s*([1-9]|[12]\d)((?:\.\d{1,2}){1,4})\.?\s+([A-Z][^\n]{2,110})$',
    re.MULTILINE)
#  pola tambahan: bab romawi & lampiran (untuk gambaran bentuk naskah)
POLA_BAB = re.compile(r'^\s*(?:BAB|Bab)\s+([IVX]+|\d+)\b', re.MULTILINE)


def teks(path: Path) -> str:
    try:
        import fitz                                   # PyMuPDF
        d = fitz.open(path)
        t = '\n'.join(p.get_text() for p in d)
        d.close()
        return t
    except Exception as e:                                # noqa: BLE001
        return f'__GALAT__{type(e).__name__}: {e}'


def kedalaman(sub: str) -> int:
    return len([x for x in sub.strip('.').split('.') if x])


berkas = sorted(PETA.glob('*.pdf'))
print('═' * 108)
print(f'  UKUR KEDALAMAN PETA — {len(berkas)} naskah NYATA (repo kampus)')
print('═' * 108)

baris, ring = [], {'baca': 0, 'galat': 0, 'kosong': 0, 'scan': 0,
                   'lama': 0, 'baru': 0, 'd2': 0, 'd3': 0, 'd4': 0,
                   'bab': 0, 'n_punya3': 0, 'n_punya4': 0, 'n_naik': 0}

for p in berkas:
    t = teks(p)
    if t.startswith('__GALAT__'):
        ring['galat'] += 1
        continue
    kar = len(t.strip())
    if kar < 500:
        ring['scan'] += 1                     # PDF scan / tak ada teks
        continue
    ring['baca'] += 1

    lama = sorted({f'{m.group(1)}.{m.group(2)}' for m in POLA_LAMA.finditer(t)})
    baru = sorted({f'{m.group(1)}{m.group(2)}' for m in POLA_BARU.finditer(t)})
    d2 = sum(1 for x in baru if kedalaman(x) == 2)
    d3 = sum(1 for x in baru if kedalaman(x) == 3)
    d4 = sum(1 for x in baru if kedalaman(x) >= 4)
    bab = len(POLA_BAB.findall(t))

    ring['lama'] += len(lama)
    ring['baru'] += len(baru)
    ring['d2'] += d2
    ring['d3'] += d3
    ring['d4'] += d4
    ring['bab'] += bab
    if d3:
        ring['n_punya3'] += 1
    if d4:
        ring['n_punya4'] += 1
    if len(baru) > len(lama):
        ring['n_naik'] += 1

    baris.append({'nama': p.name, 'kar': kar, 'lama': len(lama), 'baru': len(baru),
                  'd2': d2, 'd3': d3, 'd4': d4, 'bab': bab})

print(f"\n  naskah terbaca : {ring['baca']}   scan/kosong: {ring['scan']}   "
      f"galat: {ring['galat']}")
print(f"  total sub-bab  : LAMA {ring['lama']}  →  BARU {ring['baru']}")
print(f"  rincian        : 2 tingkat {ring['d2']} · 3 tingkat {ring['d3']} · "
      f"4+ tingkat {ring['d4']}")
print(f"  bab romawi/arab: {ring['bab']}")
print(f"  naskah PUNYA 3 tingkat: {ring['n_punya3']}   PUNYA 4+ tingkat: "
      f"{ring['n_punya4']}   NAIK: {ring['n_naik']}")

tot = max(1, ring['baca'])
print(f"\n  PERSENTASE dari {ring['baca']} naskah terbaca:")
print(f"    punya sub-sub bab (3 tingkat) : "
      f"{ring['n_punya3']}/{ring['baca']} = {100*ring['n_punya3']//tot}%")
print(f"    punya 4+ tingkat              : "
      f"{ring['n_punya4']}/{ring['baca']} = {100*ring['n_punya4']//tot}%")

print('\n  ── 30 naskah teratas (nama · kar · lama · baru · d2 · d3 · d4 · bab) ──')
for b in sorted(baris, key=lambda x: -x['baru'])[:30]:
    tanda = ' ←4+' if b['d4'] else (' ←3tk' if b['d3'] else '')
    print(f"  {b['nama'][:40]:40s} {b['kar']:>7} {b['lama']:>5} {b['baru']:>5} "
          f"{b['d2']:>4} {b['d3']:>4} {b['d4']:>3} {b['bab']:>4}{tanda}")

Path('/opt/data/services/eduai-publishing/_arsip/ukur_kedalaman_97.json').write_text(
    json.dumps({'ringkas': ring, 'baris': baris}, ensure_ascii=False, indent=1))
print('\n  hasil → _arsip/ukur_kedalaman_97.json')
