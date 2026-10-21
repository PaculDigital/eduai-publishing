#!/usr/bin/env python3
"""UJI BANDING 3 PEMBACA PDF (05Okt26, putusan Bos "A").

Yang dibandingkan pada 97 naskah NYATA:
  1. PyMuPDF (fitz)    — dipakai host/alat uji sekarang
  2. pypdf             — dipakai CONTAINER produksi sekarang
  3. PyPDFium2         — calon pengganti

YANG DIUKUR (bukan opini):
  · kecepatan (detik per naskah)
  · panjang teks hasil (karakter)
  · jumlah sub-bab 2/3/4 tingkat yang TERTANGKAP (yang paling penting!)
  · jumlah galat / teks kosong
  · ukuran paket (MB)
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

PETA = Path('/opt/data/services/eduai-publishing/_contoh-dokumen/uji-kedalaman')
KEL = Path('/opt/data/services/eduai-publishing/_arsip')

POLA_LAMA = re.compile(r'^\s*([1-9]|[12]\d)\.(\d{1,2})\.?\s+([A-Z][^\n]{2,110})$',
                       re.MULTILINE)
POLA_BARU = re.compile(
    r'^\s*([1-9]|[12]\d)((?:\.\d{1,2}){1,4})\.?\s+([A-Z][^\n]{2,110})$',
    re.MULTILINE)


def kedalaman(x: str) -> int:
    return len([p for p in x.strip('.').split('.') if p])


def ukur(teks: str) -> dict:
    lama = len({f'{m.group(1)}.{m.group(2)}' for m in POLA_LAMA.finditer(teks)})
    baru = sorted({f'{m.group(1)}{m.group(2)}' for m in POLA_BARU.finditer(teks)})
    return {'kar': len(teks.strip()), 'lama': lama, 'baru': len(baru),
            'd2': sum(1 for x in baru if kedalaman(x) == 2),
            'd3': sum(1 for x in baru if kedalaman(x) == 3),
            'd4': sum(1 for x in baru if kedalaman(x) >= 4)}


# ── 3 pembaca ────────────────────────────────────────────────────────────
def pakai_fitz(p: Path) -> str:
    import fitz
    with fitz.open(p) as d:
        return '\n'.join(h.get_text() for h in d)


def pakai_pypdf(p: Path) -> str:
    from pypdf import PdfReader
    return '\n'.join((h.extract_text() or '') for h in PdfReader(str(p)).pages)


def pakai_pdfium(p: Path) -> str:
    import pypdfium2 as pdfium
    d = pdfium.PdfDocument(str(p))
    keluar = []
    for i in range(len(d)):
        h = d[i]
        tp = h.get_textpage()
        keluar.append(tp.get_text_range())
        tp.close()
        h.close()
    d.close()
    return '\n'.join(keluar)


PEMBACA = [
    ('PyMuPDF (fitz)', pakai_fitz),
    ('pypdf (produksi)', pakai_pypdf),
    ('PyPDFium2 (calon)', pakai_pdfium),
]

berkas = sorted(PETA.glob('*.pdf'))
print('═' * 108)
print(f'  UJI BANDING 3 PEMBACA PDF — {len(berkas)} naskah nyata')
print('═' * 108)

ringkas = {}
for nama, fungsi in PEMBACA:
    t0 = time.time()
    tot = {'kar': 0, 'lama': 0, 'baru': 0, 'd2': 0, 'd3': 0, 'd4': 0}
    galat, kosong, n = 0, 0, 0
    for p in berkas:
        try:
            t = fungsi(p)
        except Exception:                                     # noqa: BLE001
            galat += 1
            continue
        if len(t.strip()) < 500:
            kosong += 1
            continue
        n += 1
        u = ukur(t)
        for k in tot:
            tot[k] += u[k]
    dt = time.time() - t0
    ringkas[nama] = {'detik': round(dt, 1), 'per_naskah': round(dt / max(1, len(berkas)), 3),
                     'terbaca': n, 'galat': galat, 'kosong': kosong, **tot}
    print(f"\n  {nama}")
    print(f"    waktu     : {dt:.1f} dtk total · {dt/max(1,len(berkas)):.3f} dtk/naskah")
    print(f"    terbaca   : {n}   galat: {galat}   kosong/scan: {kosong}")
    print(f"    karakter  : {tot['kar']:,}")
    print(f"    sub-bab   : lama {tot['lama']} · baru {tot['baru']} "
          f"(2tk {tot['d2']} · 3tk {tot['d3']} · 4tk {tot['d4']})")

# ukuran paket
import subprocess                                          # noqa: E402
print('\n  ── ukuran paket terpasang ──')
for nama_pak in ('pymupdf', 'pypdf', 'pypdfium2'):
    r = subprocess.run(['/opt/data/.venv/bin/python3', '-c',
                        f'import importlib.util,os;'
                        f's=importlib.util.find_spec("{nama_pak}");'
                        f'print(os.path.dirname(s.origin) if s else "?")'],
                       capture_output=True, text=True)
    jalur = r.stdout.strip()
    mb = 0.0
    if jalur and jalur != '?':
        p = Path(jalur).parent if Path(jalur).name != 'pypdf' else Path(jalur)
        try:
            mb = sum(f.stat().st_size for f in p.rglob('*')
                     if f.is_file()) / 1_048_576
        except Exception:                                     # noqa: BLE001
            pass
    print(f'    {nama_pak:12s} {mb:7.1f} MB')

(KEL / 'uji_banding_pdf.json').write_text(
    json.dumps(ringkas, ensure_ascii=False, indent=1))
print('\n  hasil → _arsip/uji_banding_pdf.json')
