#!/usr/bin/env python3
"""UJI BERGIGI pembaca PDF EduAi (05Okt26, putusan Bos "B").

Membuktikan 3 hal:
  1. pypdfium2 ADA    → DIPAKAI (bukan pypdf)
  2. pypdfium2 HILANG → jatuh ke pypdf, hasil tetap ada
  3. keduanya hilang  → balik '' (tidak meledak, tidak ngarang)

Cara pastikan "yang dipakai pypdfium2": suntik penghitung import —
pypdfium2 dibungkus supaya mencatat pemakaiannya.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, '/app')
PDF = Path('/tmp/uji.pdf')
if not PDF.exists():
    print('  ❌ PDF uji tidak ada di /tmp/uji.pdf')
    raise SystemExit(1)

LULUS = GAGAL = 0


def cek(nama: str, syarat: bool, ket: str = '') -> None:
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama} {ket}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama} {ket}')


# ── 1. pypdfium2 ADA → harus DIPAKAI ─────────────────────────────────────
import pypdfium2 as _asli                                # noqa: E402

PENANDA = {'pypdfium2': 0, 'pypdf': 0}


class _PDFiumPalsu:
    """Bungkus pypdfium2 supaya pemakaiannya tercatat."""

    def __init__(self, *a, **k):
        PENANDA['pypdfium2'] += 1
        self._d = _asli.PdfDocument(*a, **k)

    def __len__(self):
        return len(self._d)

    def __getitem__(self, i):
        return self._d[i]

    def __getattr__(self, n):
        return getattr(self._d, n)


sys.modules['pypdfium2'] = type(sys)('pypdfium2')
sys.modules['pypdfium2'].PdfDocument = _PDFiumPalsu
sys.modules['pypdfium2'].__getattr__ = lambda n: getattr(_asli, n)

import app.ai as A                                        # noqa: E402

t1 = A._teks_dari_berkas(PDF, 'uji.pdf')
cek('pypdfium2 ADA → dipakai', PENANDA['pypdfium2'] == 1,
    f"(dipakai {PENANDA['pypdfium2']}×)")
cek('hasil teks TIDAK kosong', len(t1) > 500, f"({len(t1):,} kar)")

# ── 2. pypdfium2 HILANG → jatuh ke pypdf ────────────────────────────────
import importlib                                         # noqa: E402

sys.modules['pypdfium2'] = None
importlib.reload(A)
t2 = A._teks_dari_berkas(PDF, 'uji.pdf')
cek('pypdfium2 hilang → jatuh ke pypdf', len(t2) > 500, f"({len(t2):,} kar)")
cek('hasil dua jalur SETARA (±5%)',
    abs(len(t1) - len(t2)) / max(1, len(t1)) < 0.05,
    f"(beda {abs(len(t1)-len(t2)):,} kar)")

# ── 3. keduanya hilang → '' (tidak meledak) ─────────────────────────────
sys.modules['pypdf'] = None
importlib.reload(A)
t3 = A._teks_dari_berkas(PDF, 'uji.pdf')
cek('keduanya hilang → balik "" (tidak meledak)', t3 == '',
    f"(hasil {len(t3)} kar)")

print(f'\n  LULUS {LULUS} / GAGAL {GAGAL}')
raise SystemExit(1 if GAGAL else 0)
