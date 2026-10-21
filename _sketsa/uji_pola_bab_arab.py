#!/usr/bin/env python3
"""UKUR: pola bab dengan ANGKA ARAB ("BAB 1") — 05Okt26.

AKAR: _POLA_BAB hanya menerima romawi [IVXLC] → naskah ber-"BAB 1" = 0 bab.

Ukur DUA arah pada 18 naskah ASLI:
  (a) bab BARU yang tertangkap  → harus > 0
  (b) SAMPAH                    → harus ~0

Bahaya angka Arab (BUKAN pada romawi):
  · "BAB 1" di DAFTAR ISI  → sudah dibuang buang_daftar_isi
  · "lihat BAB 2" (kutipan) → harus ditolak
  · "Tabel 1", "Gambar 1"   → tidak diawali "BAB", aman
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app.ai import _teks_dari_berkas                        # noqa: E402
from app.state import (buang_daftar_isi, deteksi_bab_besar,  # noqa: E402
                       _POLA_BARIS_SAMPAH)

KEL1 = Path('/app/_contoh-dokumen/tesis-bos-gdrive')
KEL2 = Path('/app/_contoh-dokumen')

POLA_ARAB = re.compile(r'^[ \t]*(?i:BAB)[ \t]+(\d{1,2})[ \t]*(.*)$', re.MULTILINE)

berkas = sorted(KEL1.glob('*.pdf'))
berkas += [p for p in sorted(KEL2.glob('*/*.docx'))]
berkas += [p for p in sorted(KEL2.glob('*/*.txt'))]

print('═' * 94)
print(f'  UJI POLA "BAB <angka arab>" — {len(berkas)} naskah ASLI')
print('═' * 94)
print()

gain = 0
kotor = 0
for p in berkas:
    try:
        t = _teks_dari_berkas(p, p.name)
    except Exception:                                          # noqa: BLE001
        continue
    if not t.strip():
        continue
    bersih = buang_daftar_isi(t)
    lama = {b['section_id'] for b in deteksi_bab_besar(t)}
    n_lama = len(lama)

    kandidat = []
    for m in POLA_ARAB.finditer(bersih):
        nomor, judul = m.group(1), (m.group(2) or '').strip()
        if judul and _POLA_BARIS_SAMPAH.match(judul):
            kotor += 1
            continue
        kandidat.append((nomor, judul))

    if not kandidat:
        continue
    baru = [k for k in kandidat if f'BAB {k[0]}' not in lama]
    print(f'── {p.name[:40]:42} lama={n_lama} → arab={len(kandidat)} '
          f'(baru={len(baru)})')
    for nomor, judul in kandidat[:7]:
        tanda = ' ← BARU' if f'BAB {nomor}' not in lama else ''
        print(f'      BAB {nomor}  {judul[:44]}{tanda}')
    gain += len(baru)
    print()

print('═' * 94)
print(f'  bab BARU yang tertangkap : {gain}')
print(f'  ditolak sebagai sampah   : {kotor}')
print('═' * 94)
