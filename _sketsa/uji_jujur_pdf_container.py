#!/usr/bin/env python3
"""UJI BANDING JUJUR: pypdf DARI DALAM CONTAINER vs PyPDFium2 (05Okt26).

KOREKSI: putaran-1 Wulan salah — `pypdf` dipanggil dari venv host yang
MEMANG tidak punya pypdf → "0 terbaca" itu PALSU. Yang benar: pypdf
dijalankan DI DALAM container (tempat ia benar-benar dipakai user).

Jalankan DI DALAM container: docker exec eduai-app python3 /app/uji_jujur_pdf.py
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

PETA = Path('/app/_naskah_uji_teks')          # teks hasil PyMuPDF (host)
PDF = Path('/app/_naskah_uji')                # PDF nyata (untuk pypdf)

POLA_LAMA = re.compile(r'^\s*([1-9]|[12]\d)\.(\d{1,2})\.?\s+([A-Z][^\n]{2,110})$',
                       re.MULTILINE)
POLA_BARU = re.compile(
    r'^\s*([1-9]|[12]\d)((?:\.\d{1,2}){1,4})\.?\s+([A-Z][^\n]{2,110})$',
    re.MULTILINE)


def ukur(teks: str) -> dict:
    def dlm(x):
        return len([p for p in x.strip('.').split('.') if p])
    lama = len({f'{m.group(1)}.{m.group(2)}' for m in POLA_LAMA.finditer(teks)})
    baru = sorted({f'{m.group(1)}{m.group(2)}' for m in POLA_BARU.finditer(teks)})
    return {'kar': len(teks.strip()), 'lama': lama, 'baru': len(baru),
            'd2': sum(1 for x in baru if dlm(x) == 2),
            'd3': sum(1 for x in baru if dlm(x) == 3),
            'd4': sum(1 for x in baru if dlm(x) >= 4)}


def pakai_pypdf(p: Path) -> str:
    from pypdf import PdfReader
    return '\n'.join((h.extract_text() or '') for h in PdfReader(str(p)).pages)


pdfs = sorted(PDF.glob('*.pdf'))
print('═' * 100)
print(f'  UJI JUJUR: pypdf DARI DALAM CONTAINER — {len(pdfs)} PDF')
print('═' * 100)

import pypdf                                                # noqa: E402
print(f"  versi pypdf: {getattr(pypdf, '__version__', '?')}")

t0 = time.time()
tot = {'kar': 0, 'lama': 0, 'baru': 0, 'd2': 0, 'd3': 0, 'd4': 0}
galat, kosong, n = 0, 0, 0
for p in pdfs:
    try:
        t = pakai_pypdf(p)
    except Exception as e:                                    # noqa: BLE001
        galat += 1
        print(f'    GALAT {p.name[:34]}: {type(e).__name__}')
        continue
    if len(t.strip()) < 500:
        kosong += 1
        continue
    n += 1
    u = ukur(t)
    for k in tot:
        tot[k] += u[k]
dt = time.time() - t0

print(f'\n  pypdf (dalam container)')
print(f'    waktu    : {dt:.1f} dtk · {dt/max(1,len(pdfs)):.3f} dtk/naskah')
print(f'    terbaca  : {n}   galat: {galat}   kosong/scan: {kosong}')
print(f'    karakter : {tot["kar"]:,}')
print(f'    sub-bab  : lama {tot["lama"]} · baru {tot["baru"]} '
      f'(2tk {tot["d2"]} · 3tk {tot["d3"]} · 4tk {tot["d4"]})')
