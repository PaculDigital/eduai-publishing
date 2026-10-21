#!/usr/bin/env python3
"""UJI E2E — apakah ai.py BENAR-BENAR memakai PETA PARAGRAF?

CARA BUKTI (bukan tebakan): jalankan _revisi_kerja() seperti produksi,
lalu BACA LOG — harus muncul baris:
   '[ai] PETA PARAGRAF dipakai untuk <bab> (sasaran P-xx dari N paragraf…)'
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, '/app')
os.environ.setdefault('EDUAI_DATA_DIR', '/app/data')

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s %(name)s: %(message)s')
from app import ai as A                                     # noqa: E402
from app import state as ST                                 # noqa: E402

naskah = A._teks_dari_berkas(Path('/app/_naskah_bos_uji.docx'),
                             '_naskah_bos_uji.docx')
bersih = ST.buang_daftar_isi(naskah)
peta = ST.petakan(bersih)
target = next(x for x in peta if str(x.get('section_id')) == '1.5')
isi = str(target.get('isi_teks', ''))

print('══ UJI: apakah produksi memakai PETA PARAGRAF? ══')
print(f'  naskah {len(naskah):,} kar · bagian 1.5 {len(isi):,} kar')

#  perintah = komentar pembimbing yang MENYEBUT isi paragraf (agar
#  cari_bagian bisa menemukan sasaran)
par = __import__('app.konteks', fromlist=['x']).petakan_paragraf(isi)
idx = max(range(len(par)), key=lambda i: len(par[i]['teks']))
komentar = ('Perbaiki paragraf ini supaya kalimatnya lebih mengalir: '
            + par[idx]['teks'][:60])

print(f'  komentar: "{komentar[:80]}…"')
print(f'  (paragraf sasaran sebenarnya: {par[idx]["label"]})')
print()

hasil = asyncio.run(A._revisi_kerja(
    naskah=isi,
    bab='1.5',
    komentar=[komentar],
    kepala='',
    db=None,
    fb=None,
    sebelum='',
    sesudah='',
))
print()
print('══ HASIL ══')
if isinstance(hasil, tuple):
    for i, h in enumerate(hasil):
        if isinstance(h, str):
            print(f'  [{i}] str {len(h):,} kar')
        elif isinstance(h, dict):
            print(f'  [{i}] dict kunci: {list(h.keys())[:12]}')
        elif isinstance(h, list):
            print(f'  [{i}] list {len(h)} item')
        else:
            print(f'  [{i}] {type(h).__name__}: {str(h)[:120]}')
else:
    print(f'  {type(hasil).__name__}: {str(hasil)[:300]}')