#!/usr/bin/env python3
"""UKUR KEDALAMAN pada NASKAH ASLI EduAi (05Okt26, arahan Bos).

Bos: "Buang saja naskah yang banyak itu tidak berguna. Kita akan salah terus
kalo pakai uji itu. Pakai uji skripsi dulu yang saya kasih kemarin itu lengkap."

SEBAB: naskah dari repository kampus = POTONGAN (Bab 1-2 saja). Mengukur
kedalaman dari potongan = menipu diri. Naskah ASLI EduAi (diunggah user
sungguhan) = UTUH → angka bisa dipercaya.

Dijalankan DI DALAM container (punya python-docx) untuk .docx.
"""
from __future__ import annotations

import re
import sys

sys.path.insert(0, '/app')
from app.state import (buang_daftar_isi, deteksi_bab_besar,   # noqa: E402
                       deteksi_subbab)

BERKAS = [
    '/app/_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx',
    '/app/_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unhas-olahraga-menstruasi.docx',
    '/app/_contoh-dokumen/tesis-s2/TESIS-S2-unhas-manajemen-digital-marketing.docx',
    '/app/_contoh-dokumen/tesis-s2/TESIS-S2-unhas-pendidikan-bahasa.docx',
    '/app/_contoh-dokumen/disertasi-s3/DISERTASI-S3-unhas-kesehatan-stunting.docx',
    '/app/_contoh-dokumen/skripsi-s1/NASKAH-ASLI-file47-65826kar.txt',
]

POLA = re.compile(
    r'^\s*([1-9]|[12]\d)((?:\.\d{1,2}){1,4})\.?\s+([A-Z][^\n]{2,110})$',
    re.MULTILINE)


def dlm(x: str) -> int:
    return len([p for p in x.strip('.').split('.') if p])


def teks_dari(p: str) -> str:
    if p.endswith('.txt'):
        return open(p, encoding='utf-8', errors='ignore').read()
    #  pakai fungsi BAWAAN EduAi (tanpa python-docx) — sama dengan produksi
    from pathlib import Path
    from app.ai import _teks_dari_berkas
    return _teks_dari_berkas(Path(p), p.rsplit('/', 1)[-1])


print('═' * 100)
print('  UKUR KEDALAMAN — NASKAH ASLI EduAi (utuh, bukan internet)')
print('═' * 100)
print()

for p in BERKAS:
    nama = p.rsplit('/', 1)[-1]
    try:
        t = teks_dari(p)
    except Exception as e:                                    # noqa: BLE001
        print(f'  [GALAT] {nama}: {type(e).__name__}: {e}')
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
        if d >= 3 and len(contoh) < 4:
            contoh.append(f'{nomor} {m.group(3).strip()[:46]}')

    print(f'── {nama}')
    print(f'     panjang       : {len(t):,} kar   | sesudah buang D.I: {len(bersih):,}')
    print(f'     BAB besar     : {len(bab)} → '
          + ', '.join(b["section_id"] for b in bab[:8]))
    print(f'     sub-bab (mesin): {len(sub)}')
    print(f'     KEDALAMAN     : ' + (' · '.join(f'{k}tk={v}' for k, v in sorted(ked.items()))
                                     or 'tidak ada'))
    for c in contoh:
        print(f'        · {c}')
    print()
