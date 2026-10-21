#!/usr/bin/env python3
"""UKUR: apakah pola "V. JUDUL" (romawi TITIK tanpa kata BAB) AMAN? (05Okt26)

SEBELUM menambah pola ke produksi, ukur 2 arah pada 11 tesis Bos + 6 naskah
asli:
  (a) BERAPA bab BARU yang tertangkap  → harus > 0 (gunanya)
  (b) BERAPA yang SAMPAH               → harus ~0 (bahayanya)

Bentuk berbahaya: baris daftar pustaka ("T. Rajagrafindo"), singkatan,
"V. HASIL", tapi juga "I. PENDAHULUAN" di dalam kutipan.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app.ai import _teks_dari_berkas                        # noqa: E402
from app.state import buang_daftar_isi, deteksi_bab_besar    # noqa: E402

KEL1 = Path('/app/_contoh-dokumen/tesis-bos-gdrive')
KEL2 = Path('/app/_contoh-dokumen')

#  USULAN: romawi TITIK di awal baris + judul HURUF BESAR
#  🚨 05Okt26: WAJIB tahan '\r' (PDF) — pelajaran putaran-1 (uji 0 palsu).
POLA_USUL = re.compile(
    r'^[ \t]*([IVXLC]{1,5})\.[ \t]+([A-Z][A-Z0-9 ,\-]{3,70})[ \t]*\r?$',
    re.MULTILINE)

#  kata yang menandakan BUKAN judul bab
_BUKAN = re.compile(
    r'\b(dalam|pada|menurut|adalah|yaitu|seperti|kutipan|lihat|vol|no|'
    r'press|publisher|penerbit|rajagrafindo|eds?|hlm)\b', re.I)

berkas = sorted(KEL1.glob('*.pdf')) + sorted(KEL2.glob('*/*.docx'))
berkas += [p for p in KEL2.glob('*/*.txt')]

print('═' * 96)
print(f'  UJI POLA "ROMAWI TITIK" — {len(berkas)} naskah ASLI')
print('═' * 96)
print()

gain_total = 0
ragu_total = 0
for p in berkas:
    try:
        t = _teks_dari_berkas(p, p.name)
    except Exception:                                          # noqa: BLE001
        continue
    if not t.strip():
        continue
    bersih = buang_daftar_isi(t)
    lama = {b['section_id'] for b in deteksi_bab_besar(t)}

    kandidat = []
    for m in POLA_USUL.finditer(bersih):
        romawi, judul = m.group(1), m.group(2).strip()
        if _BUKAN.search(judul):
            continue
        kandidat.append(f'{romawi}. {judul[:40]}')

    baru = [k for k in kandidat if f'BAB {k.split(".")[0]}' not in lama]
    if kandidat:
        print(f'── {p.name[:42]:44} lama BAB={len(lama)} → kandidat baru={len(baru)}')
        for k in kandidat[:6]:
            print(f'      · {k}')
        gain_total += len(baru)
        ragu_total += len(kandidat) - len(baru)
        print()

print('═' * 96)
print(f'  bab BARU yang akan tertangkap : {gain_total}')
print(f'  (yang sudah tertangkap lama)  : {ragu_total}')
print('═' * 96)
