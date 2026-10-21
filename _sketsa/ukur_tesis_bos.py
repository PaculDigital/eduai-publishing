#!/usr/bin/env python3
"""UKUR KEDALAMAN 12 tesis GDrive Bos (05Okt26).

Naskah Bos = naskah asli (utuh). Pakai fungsi BAWAAN EduAi supaya angka
yang diukur = angka yang dilihat PRODUKSI.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app.ai import _teks_dari_berkas                        # noqa: E402
from app.state import (buang_daftar_isi, deteksi_bab_besar,  # noqa: E402
                       deteksi_subbab)

KEL = Path('/app/_contoh-dokumen/tesis-bos-gdrive')
POLA = re.compile(
    r'^\s*([1-9]|[12]\d)((?:\.\d{1,2}){1,4})\.?\s+([A-Z][^\n]{2,110})$',
    re.MULTILINE)


def dlm(x: str) -> int:
    return len([p for p in x.strip('.').split('.') if p])


berkas = sorted(KEL.glob('*.pdf'))
print('═' * 96)
print(f'  UKUR KEDALAMAN — {len(berkas)} TESIS BOS (GDrive)')
print('═' * 96)
print()

ringkas = []
for p in berkas:
    t = _teks_dari_berkas(p, p.name)
    if not t.strip():
        print(f'── {p.name}: TIDAK TERBACA (scan?)')
        continue
    bersih = buang_daftar_isi(t)
    bab = deteksi_bab_besar(t)
    sub = deteksi_subbab(t)
    ked: dict[int, int] = {}
    contoh: list[str] = []
    for m in POLA.finditer(bersih):
        nomor = f'{m.group(1)}{m.group(2)}'
        d = dlm(nomor)
        ked[d] = ked.get(d, 0) + 1
        if d >= 3 and len(contoh) < 3:
            contoh.append(f'{nomor} {m.group(3).strip()[:44]}')

    ringkas.append((p.name, len(t), len(bab), len(sub), ked))
    print(f'── {p.name}')
    print(f'     panjang    : {len(t):,} kar')
    print(f'     BAB besar  : {len(bab)} → ' + ', '.join(b['section_id'] for b in bab[:7]))
    print(f'     sub-bab    : {len(sub)}  (mesin)')
    print(f'     KEDALAMAN  : ' + (' · '.join(f'{k}tk={v}' for k, v in sorted(ked.items()))
                                    or 'TIDAK ADA'))
    for c in contoh:
        print(f'        · {c}')
    print()

print('═' * 96)
print('  RINGKASAN')
print('═' * 96)
print(f'  {"berkas":20} {"kar":>9} {"BAB":>4} {"sub":>5}  kedalaman')
for nama, kar, nb, ns, kd in ringkas:
    k = ' · '.join(f'{a}tk={b}' for a, b in sorted(kd.items())) or '—'
    print(f'  {nama:20} {kar:>9,} {nb:>4} {ns:>5}  {k}')

n_ada = sum(1 for _, _, _, _, kd in ringkas if any(a >= 3 for a in kd))
print()
print(f'  punya sub-sub (3+ tingkat): {n_ada}/{len(ringkas)}')
