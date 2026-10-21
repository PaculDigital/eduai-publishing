#!/usr/bin/env python3
"""CEK: NASKAH-file47 → 5 atau 6 bab yang BENAR? (05Okt26)."""
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app.ai import _teks_dari_berkas                        # noqa: E402
from app.state import _POLA_BAB, buang_daftar_isi            # noqa: E402

for p in Path('/app/_contoh-dokumen').glob('*/*file47*'):
    print('berkas:', p.name)
    t = _teks_dari_berkas(p, p.name)
    b = buang_daftar_isi(t)
    print('=== SEMUA baris BAB <nomor> ===')
    for m in _POLA_BAB.finditer(b):
        print('   ', repr(m.group(0)[:74]))
