"""UKUR: sedalam apa deteksi sub-bab SEKARANG vs YANG SEHARUSNYA (05Okt26).

TUJUAN (putusan Bos 4A "ukur dulu"): sebelum memperdalam peta halus sampai
sub-sub bab, UKUR dulu berapa yang ketemu & berapa yang salah.

YANG DIUKUR (per naskah):
  1. sub-bab 2 tingkat (2.3)   → pola LAMA (`_POLA_SUBBAB`)
  2. sub-sub bab 3 tingkat (2.3.1) → apakah ADA di naskah & terbaca?
  3. sub-sub-sub 4 tingkat (2.3.1.1)
  4. Berapa yang TIDAK terbaca (lubang nyata)

CARA: hitung dari TEKS langsung (regex), bukan dari AI — jadi gratis &
deterministik. Yang diukur = KEMAMPUAN POLA, bukan mutu AI.
"""
import json
import os
import re
import sys

sys.path.insert(0, '/app')

from app import state  # noqa: E402

#  pola LAMA (dari state.py:_POLA_SUBBAB) — yang dipakai produksi sekarang
POLA_LAMA = re.compile(r'^\s*([1-9]|[12]\d)\.(\d{1,2})\.?\s+([A-Z][^\n]{2,110})$',
                       re.MULTILINE)
#  pola BARU yang diusulkan: 2.3.1 / 2.3.1.1 (kedalaman berapa pun)
POLA_BARU = re.compile(r'^\s*([1-9]|[12]\d)((?:\.\d{1,2}){1,4})\.?\s+([A-Z][^\n]{2,110})$',
                       re.MULTILINE)

DOK = '/app/uploads'


def teks_dari(berkas: str) -> str:
    """Ambil teks naskah (docx/txt) memakai fungsi produksi.

    ⚠️ `app.ai._teks_dari_berkas(p, nama)` minta **Path**, bukan bytes
    (kesalahan alat ukur putaran-1 — 58 naskah "GALAT" palsu).
    """
    try:
        from pathlib import Path
        from app.ai import _teks_dari_berkas          # noqa: PLC0415
        return _teks_dari_berkas(Path(berkas), os.path.basename(berkas)) or ''
    except Exception as e:                                # noqa: BLE001
        return f'__GALAT__{type(e).__name__}: {e}'


def kedalaman(sub: str) -> int:
    """'2.3' → 2 tingkat · '2.3.1' → 3 · '2.3.1.1' → 4."""
    return len([x for x in sub.strip('.').split('.') if x])


kumpul = []
for akar, _dirs, berkas_list in os.walk(DOK):
    for b in berkas_list:
        if b.lower().endswith(('.docx', '.txt')):
            kumpul.append(os.path.join(akar, b))

print('═' * 100)
print(f'  UKUR KEDALAMAN DETEKSI SUB-BAB — {len(kumpul)} naskah asli')
print('═' * 100)

ringkas = {'baca': 0, 'galat': 0, 'kosong': 0,
           'd2': 0, 'd3': 0, 'd4p': 0,
           'lama': 0, 'baru': 0, 'tambah': 0, 'naskah_naik': 0}
baris = []

for jalur in sorted(kumpul):
    teks = teks_dari(jalur)
    nama = os.path.basename(jalur)
    if teks.startswith('__GALAT__'):
        ringkas['galat'] += 1
        baris.append((nama, 'GALAT', 0, 0, 0, 0, teks[:40]))
        continue
    if not teks.strip():
        ringkas['kosong'] += 1
        continue
    ringkas['baca'] += 1

    lama = sorted({f'{m.group(1)}.{m.group(2)}' for m in POLA_LAMA.finditer(teks)})
    baru = sorted({f'{m.group(1)}{m.group(2)}' for m in POLA_BARU.finditer(teks)})
    d2 = sum(1 for x in baru if kedalaman(x) == 2)
    d3 = sum(1 for x in baru if kedalaman(x) == 3)
    d4p = sum(1 for x in baru if kedalaman(x) >= 4)

    ringkas['lama'] += len(lama)
    ringkas['baru'] += len(baru)
    ringkas['tambah'] += max(0, len(baru) - len(lama))
    if d3 or d4p:
        ringkas['naskah_naik'] += 1
    if d3:
        ringkas['d3'] += d3
    if d4p:
        ringkas['d4p'] += d4p
    if d2:
        ringkas['d2'] += d2

    baris.append((nama, len(teks), len(lama), len(baru), d2, d3, d4p))

print(f'\n  naskah terbaca : {ringkas["baca"]}   galat: {ringkas["galat"]}   '
      f'kosong: {ringkas["kosong"]}')
print(f'  total sub-bab  : POLA LAMA {ringkas["lama"]}  →  POLA BARU {ringkas["baru"]}  '
      f'(+{ringkas["tambah"]})')
print(f'  rincian BARU   : 2 tingkat {ringkas["d2"]} · 3 tingkat {ringkas["d3"]} · '
      f'4+ tingkat {ringkas["d4p"]}')
print(f'  naskah yang NAIK karena lebih dalam: {ringkas["naskah_naik"]}')

print('\n  ── 25 naskah teratas (nama · kar · lama · baru · d2 · d3 · d4+) ──')
for n, kar, la, ba, a2, a3, a4 in sorted(baris, key=lambda x: -x[3])[:25]:
    if n == 'GALAT':
        continue
    tanda = '  ← NAIK' if a3 or a4 else ''
    print(f'  {n[:44]:44s} {kar:>8} {la:>5} {ba:>5} {a2:>4} {a3:>4} {a4:>4}{tanda}')

with open('/app/_hasil_ukur_subbab.json', 'w') as f:
    json.dump({'ringkas': ringkas,
               'baris': [{'nama': b[0], 'kar': b[1], 'lama': b[2], 'baru': b[3],
                          'd2': b[4], 'd3': b[5], 'd4': b[6]}
                         for b in baris if b[1] != 'GALAT']}, f, ensure_ascii=False)
print('\n  hasil JSON → /app/_hasil_ukur_subbab.json')
