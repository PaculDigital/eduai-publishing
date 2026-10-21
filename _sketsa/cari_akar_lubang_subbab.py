#!/usr/bin/env python3
"""CARI AKAR: kenapa naskah besar TIDAK punya sub-bab terdeteksi (05Okt26).

Ambil naskah UTUH yang `d3`=0 DAN `baru` kecil, lalu CETAK baris-baris yang
MIRIP judul bagian (diawali nomor/huruf/romawi) — untuk MELIHAT bentuk
penomoran aslinya. Menebak dilarang; ini mengukur.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

AKAR = Path('/opt/data/services/eduai-publishing')
PETA = AKAR / '_contoh-dokumen' / 'uji-kedalaman'
d = json.loads((AKAR / '_arsip/ukur_kedalaman_97.json').read_text())

# ambil naskah UTUH yang sub-sub babnya SEDIKIT (lubang)
sasaran = [b for b in d['baris'] if b['bab'] >= 3 and b['d3'] == 0]
sasaran = sorted(sasaran, key=lambda x: -x['kar'])[:6]

#  pola-pola alternatif yang MUNGKIN dipakai naskah (untuk diuji, bukan dipakai)
POLA_UJI = {
    'A.1  (huruf.angka)': r'^\s*([A-Z])\.(\d{1,2})\.?\s+\S',
    'I.1  (romawi.angka)': r'^\s*([IVX]{1,4})\.(\d{1,2})\.?\s+\S',
    '1.a  (angka.huruf)': r'^\s*(\d{1,2})\.([a-z])\.?\s+\S',
    'a.   (huruf kecil)': r'^\s*([a-z])\.\s+\S',
    '(a)  (dalam kurung)': r'^\s*\(([a-z])\)\s+\S',
    '1)   (angka tutup)': r'^\s*(\d{1,2})\)\s+\S',
    '1.2.3 tanpa judul': r'^\s*(\d{1,2}\.\d{1,2}\.\d{1,2})\s*$',
    'BAB + judul': r'^\s*BAB\s+[IVX\d]+\b',
}

print('═' * 108)
print('  CARI AKAR — naskah UTUH yang sub-sub babnya 0 (kenapa lolos?)')
print('═' * 108)

for b in sasaran:
    path = PETA / b['nama']
    if not path.exists():
        print(f'\n  (hilang: {b["nama"]})')
        continue
    try:
        import fitz
        doc = fitz.open(path)
        t = '\n'.join(p.get_text() for p in doc)
        doc.close()
    except Exception as e:                                    # noqa: BLE001
        print(f'\n  {b["nama"]}: GALAT {e}')
        continue

    print(f"\n{'─'*108}")
    print(f"  NASKAH: {b['nama'][:60]}")
    print(f"          {b['kar']:,} kar · bab={b['bab']} · pola-lama={b['lama']} "
          f"· pola-baru={b['baru']} · 3tk={b['d3']}")
    print(f"{'─'*108}")

    # uji tiap pola alternatif: berapa yang cocok?
    for nama_p, pola in POLA_UJI.items():
        n = len(re.findall(pola, t, re.MULTILINE))
        if n:
            print(f'    cocok {n:>4}×  ← {nama_p}')

    # tampilkan 12 baris yang "mirip judul bagian" untuk DILIHAT bentuknya
    print('    ── contoh baris pendek di awal naskah (kandidat judul) ──')
    kandidat = []
    for ln in t.split('\n'):
        s = ln.strip()
        if 4 <= len(s) <= 90 and re.match(r'^[A-Z0-9(]', s):
            kandidat.append(s)
        if len(kandidat) >= 600:
            break
    # buang yang jelas kalimat (banyak koma/titik)
    bersih = [k for k in kandidat if k.count(',') <= 1 and not k.endswith('.')][:14]
    for k in bersih:
        print(f'      | {k[:88]}')
