#!/usr/bin/env python3
"""SURUH JEV BEKERJA pada naskah yang MESIN GAGAL (05Okt26).

Perintah Bos: "Uji uji terus Jev gak dipakai?"

KASUS: 290465463.pdf → mesin bilang BAB=0, padahal naskahnya menulis
"BAB 1 PENDAHULUAN" ... "BAB 6 KESIMPULAN DAN SARAN".

Pertanyaan: JEV MELIHAT APA? Kalau Jev melihat bab yang mesin lewatkan,
itu BUKTI Jev berguna — dan jawaban untuk Bos.
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')
from app import satpam                                       # noqa: E402
from app.ai import _teks_dari_berkas                         # noqa: E402
from app.state import deteksi_bab_besar, deteksi_subbab, petakan  # noqa: E402
from pathlib import Path                                     # noqa: E402

KASUS = [
    ('290465463.pdf', 'mesin BAB=0, naskah tulis "BAB 1..6"'),
    ('290462754.pdf', 'mesin BAB=0, naskah tulis "IV." "V."'),
    ('290460818.pdf', 'mesin sub-bab=0'),
]

print('═' * 96)
print('  JEV MELIHAT NASKAH YANG MESIN GAGAL')
print('═' * 96)
print(f'  model: {satpam.MODEL}  ·  AKTIF: {satpam.AKTIF}')
print()

for nama, catatan in KASUS:
    p = Path('/app/_contoh-dokumen/tesis-bos-gdrive') / nama
    t = _teks_dari_berkas(p, nama)
    peta_mesin = petakan(t)
    bab_mesin = deteksi_bab_besar(t)
    sub_mesin = deteksi_subbab(t)

    h = satpam.periksa(t, peta_mesin)

    print(f'── {nama}')
    print(f'   keperluan : {catatan}')
    print(f'   MESIN     : BAB={len(bab_mesin)}  sub-bab={len(sub_mesin)} '
          f'peta={len(peta_mesin)}')
    print(f'   JEV       : jumlah_bab={h.get("jumlah_bab")} '
          f'(mesin bilang {h.get("jumlah_bab_mesin")})')
    print(f'               keyakinan={h.get("confidence")} '
          f'keputusan={h.get("keputusan")}')
    print(f'               romawi_sah={h.get("romawi_sah")} '
          f'berurutan={h.get("berurutan")}')
    print(f'               KEDALAMAN={h.get("kedalaman_subbab")}')
    print(f'               {h.get("detik")} dtk · {h.get("alasan")}')
    print()

print('═' * 96)
