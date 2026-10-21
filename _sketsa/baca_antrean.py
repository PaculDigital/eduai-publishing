"""BACA: kenapa ai_revisi masuk ANTREAN padahal antrean KOSONG?"""
import inspect
import sys

sys.path.insert(0, '/app')
from app import proses as P                                            # noqa: E402

print('KONKUREN_MAKS =', P.KONKUREN_MAKS)
print('_sedang_jalan =', P._sedang_jalan)
print('_antrean      =', list(P._antrean))
print('statistik     =', P.statistik_antrean())
print()

print('=' * 72)
print('  SUMBER _antre_atau_jalan LENGKAP')
print('=' * 72)
print(inspect.getsource(P._antre_atau_jalan))

print('=' * 72)
print('  SUMBER jalankan LENGKAP')
print('=' * 72)
print(inspect.getsource(P.jalankan))
