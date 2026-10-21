#!/usr/bin/env python3
"""MENGAPA petakan() hanya 5 bagian di naskah Bos? — UKUR, jangan menuduh.

Dugaan: naskah Bos TIDAK punya penomoran sub-bab "3.2 Judul" di teks
(hasil regex sebelumnya = 0). Atau teksnya terbaca tanpa baris terpisah.

Yang diperiksa:
   1. Apakah di TEKS hasil bacaan ada baris seperti "1.1 ..." / "3.2 ..."?
   2. Bagaimana bentuk 60 baris pertama (lihat nyata)?
   3. Apakah _POLA_SUBBAB cocok kalau diberi contoh teks normal?
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='ukur_peta_')
sys.path.insert(0, '/app')

from app import ai as A                                        # noqa: E402
from app import state as S                                     # noqa: E402

F = Path('/app/uploads/6/f920b64c1d0da1e2.docx')
t = A._teks_dari_berkas(F, F.name)

print('══ 1. BENTUK NYATA TEKS (60 baris pertama) ══')
for i, b in enumerate(t.splitlines()[:60]):
    print(f'  {i:>3}| {b[:88]}')
