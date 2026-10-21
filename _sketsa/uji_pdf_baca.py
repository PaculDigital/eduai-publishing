"""Uji _teks_dari_berkas PDF — di dalam container (deps lengkap)."""
from pathlib import Path

from app.ai import _teks_dari_berkas

t = _teks_dari_berkas(Path('/tmp/uji_naskah.pdf'), 'uji_naskah.pdf')
print('teks keluar:', len(t), 'kar')
print('ISI:', repr(t[:120]))
assert 'PENDAHULUAN' in t or 'sawit' in t, 'teks PDF tidak terbaca!'
print('PDF READER OK')
