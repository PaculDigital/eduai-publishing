#!/usr/bin/env python3
"""CARI naskah yang BENAR-BENAR berisi tulisan (bukan template).

Tanda naskah jadi:
   · BANYAK kalimat panjang (≥ 60 kar) dan tidak ada placeholder {}
   · ada paragraf berisi (bukan cuma judul)
Tanda template:
   · memuat "{JUDUL", "{NAMA", "[[TABEL-", "[[GAMBAR-"
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='cari_jadi_')
sys.path.insert(0, '/app')

from app import ai as A                                        # noqa: E402
from app import state as S                                     # noqa: E402

hasil = []
for p in list(Path('/app/uploads/6').glob('*.docx'))[:60]:
    try:
        t = A._teks_dari_berkas(p, p.name)
    except Exception:                                         # noqa: BLE001
        continue
    if not t:
        continue
    template = ('{JUDUL' in t or '{NAMA' in t or '[[TABEL-' in t
                or '[[GAMBAR-' in t)
    panjang_kalimat = [len(x) for x in t.split('. ') if len(x) > 60]
    peta = S.petakan(S.buang_daftar_isi(t))
    hasil.append((len(peta), len(panjang_kalimat), template, len(t),
                  p.name, p.stat().st_size))

#  prioritas: BUKAN template + banyak bagian + panjang
hasil.sort(key=lambda x: (not x[2], x[0], x[1]), reverse=True)
print('══ KANDIDAT NASKAH JADI (bukan template) ══')
print(f'{"peta":>5} {"kalimat":>8} {"tmpl":>5} {"teks":>8} {"byte":>9}  nama')
for pt, kl, tp, ln, nm, by in hasil[:10]:
    print(f'{pt:>5} {kl:>8} {"YA" if tp else "TIDAK":>5} {ln:>8,} {by:>9,}  {nm}')
