"""BUKTIKAN: pemecah paragraf \n{2,} TIDAK PERNAH kena pada teks dari _teks_dari_docx.

Uji 2 arah (standar Bos):
  SEHAT : teks buatan dengan \n\n  → HARUS pecah jadi banyak paragraf
  NYATA : teks dari docx Bos      → berapa paragraf?
"""
import pathlib
import re
import sys

sys.path.insert(0, '/app')
from app.ai import _teks_dari_docx                          # noqa: E402

DOCX = pathlib.Path('/app/_naskah_bos_uji.docx')


def pecah(t: str) -> list[str]:
    """PEMECAH PERSIS yang dipakai tinjau.html: split(/\\n{2,}/)."""
    return [p for p in re.split(r'\n{2,}', t) if p.strip()]


print('═' * 72)
print('A. SEHAT — teks dengan baris kosong (\\n\\n)')
print('═' * 72)
sehat = 'Paragraf satu.\n\nParagraf dua.\n\nParagraf tiga.'
print(f'   pecah → {len(pecah(sehat))} paragraf  (harus 3)')
print(f'   {"✅ BENAR" if len(pecah(sehat)) == 3 else "❌ SALAH"}')

print()
print('═' * 72)
print('B. NYATA — teks dari DOCX BOS')
print('═' * 72)
t = _teks_dari_docx(DOCX)
print(f'   panjang teks        : {len(t):,} kar')
print(f'   \\n (baris)          : {t.count(chr(10)):,}')
print(f'   \\n\\n (baris kosong)  : {t.count(chr(10) * 2):,}  ← KUNCI')
print(f'   pecah(/\\n{{2,}}/)     : {len(pecah(t))} paragraf  ← INI MASALAHNYA')
print()
print('   --- 200 kar pertama, tanda ↵ = pindah baris ---')
print('   ' + t[:200].replace('\n', '↵\n   '))

print()
print('═' * 72)
print('C. KESIMPULAN')
print('═' * 72)
n = len(pecah(t))
print(f'   DOCX asli punya 478 paragraf Word, tapi halaman menampilkan {n}.')
if n <= 5:
    print('   ⇒ BUG NYATA: pemecah \\n{2,} tidak cocok dengan keluaran')
    print('     _teks_dari_docx (yang memakai \\n TUNGGAL).')
else:
    print('   ⇒ pemecah BEKERJA — akar di tempat lain.')
