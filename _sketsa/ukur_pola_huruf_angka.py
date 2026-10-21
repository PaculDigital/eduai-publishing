#!/usr/bin/env python3
"""UKUR BAHAYA pola 'A.' dan '1)' sebagai sub-bab (05Okt26, putusan Bos "B").

BAHAYA NYATA: 'A.' & '1)' dipakai di DAFTAR PUSTAKA & daftar bernomor.
Kalau dipasang tanpa saring → daftar pustaka jadi sub-bab PALSU → HARGA SALAH.

Naskah sasaran: 290460818 & 389360758 (sub-bab=0, padahal ada 'A.'/'1)').

Uji DUA arah:
  (a) berapa sub-bab NYATA tertangkap (gunanya)
  (b) berapa SAMPAH dari daftar pustaka  (bahayanya)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app.ai import _teks_dari_berkas                        # noqa: E402
from app.state import buang_daftar_isi                       # noqa: E402

KEL = Path('/app/_contoh-dokumen/tesis-bos-gdrive')

#  usulan pola
POLA_HURUF = re.compile(r'^[ \t]*([A-Z])\.\t?[ \t]+([A-Z][^\n]{3,70})[ \t\r]*$',
                        re.MULTILINE)
POLA_ANGKA_TUTUP = re.compile(r'^[ \t]*(\d{1,2})\)[ \t]+([A-Z][^\n]{3,70})[ \t\r]*$',
                              re.MULTILINE)

#  ── penanda DAFTAR PUSTAKA (bahan saring) ────────────────────────────────
PENANDA_PUSTAKA = re.compile(
    r'\b(press|publisher|penerbit|rajagrafindo|erlangga|gramedia|'
    r'yogyakarta|jakarta|bandung|surabaya|malang|CV\.|PT\.|'
    r'eds?\.|hlm|vol\.|no\.|jurnal|skripsi|tesis|disertasi|'
    r'http|www\.|doi|ISBN|diakses)\b', re.IGNORECASE)

#  penanda kita sedang di zona DAFTAR PUSTAKA / REFERENSI
AKHIR_PUSTAKA = re.compile(
    r'^\s*(DAFTAR PUSTAKA|DAFTAR RUJUKAN|REFERENSI|REFERENCES|KEPUSTAKAAN)\s*[\r\n]',
    re.MULTILINE | re.IGNORECASE)


def _zona_pustaka(teks: str) -> int:
    """Posisi awal daftar pustaka (len(teks) kalau tak ada)."""
    m = None
    for m in AKHIR_PUSTAKA.finditer(teks):
        pass
    return m.start() if m else len(teks)


for nama in ['290460818.pdf', '389360758.pdf']:
    p = KEL / nama
    if not p.exists():
        print(f'[hilang] {nama}')
        continue
    t = _teks_dari_berkas(p, nama)
    bersih = buang_daftar_isi(t)
    ujung = _zona_pustaka(bersih)

    print('═' * 94)
    print(f'  {nama}   {len(t):,} kar   | daftar pustaka mulai di {ujung:,}')
    print('═' * 94)

    for pola, label in ((POLA_HURUF, 'A. HURUF'),
                        (POLA_ANGKA_TUTUP, '1) ANGKA TUTUP')):
        kandidat = []
        for m in pola.finditer(bersih):
            pos = m.start()
            di_pustaka = pos > ujung
            judul = m.group(2).strip()
            kotor = bool(PENANDA_PUSTAKA.search(judul))
            kandidat.append((pos, m.group(1), judul, di_pustaka, kotor))

        nyata = [k for k in kandidat if not k[3] and not k[4]]
        sampah = [k for k in kandidat if k[3] or k[4]]

        print(f'\n  ── {label}: total {len(kandidat)} · NYATA {len(nyata)} · '
              f'SAMPAH {len(sampah)}')
        for pos, nomor, judul, dp, kr in nyata[:8]:
            print(f'      ✅ {nomor}. {judul[:56]}')
        for pos, nomor, judul, dp, kr in sampah[:6]:
            tag = 'di-pustaka' if dp else 'kata-pustaka'
            print(f'      ❌ [{tag}] {nomor}. {judul[:52]}')
    print()
