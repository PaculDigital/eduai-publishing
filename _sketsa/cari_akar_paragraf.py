"""AKAR: kenapa naskah jadi 1 paragraf raksasa?

Uji 3 lapis, satu per satu (jangan menebak):
  1. APAKAH DOCX ASLI punya paragraf?  → hitung <w:p> di document.xml
  2. APA yang dibaca app dari docx      → _teks_dari_docx()
  3. APA yang dikirim ke halaman        → _isi_naskah() + pemecah paragraf
"""
import pathlib
import re
import sys
import zipfile

sys.path.insert(0, '/app')

DOCX = pathlib.Path('/app/_naskah_bos_uji.docx')

print('═' * 74)
print('1. DOCX ASLI — berapa paragraf di dalamnya?')
print('═' * 74)
with zipfile.ZipFile(DOCX) as z:
    xml = z.read('word/document.xml').decode('utf-8', 'replace')
wps = re.findall(r'<w:p[ >]', xml)
print(f'   <w:p> (paragraf Word)     : {len(wps):,}')
print(f'   panjang document.xml      : {len(xml):,} kar')
wbr = re.findall(r'<w:br[^>]*>', xml)
print(f'   <w:br/> (pindah baris)    : {len(wbr):,}')
print(f'   <w:tbl> (tabel)           : {len(re.findall(r"<w:tbl[ >]", xml)):,}')

print()
print('═' * 74)
print('2. APA YANG DIBACA APP — _teks_dari_docx()')
print('═' * 74)
from app.ai import _teks_dari_docx                          # noqa: E402
t = _teks_dari_docx(DOCX)
print(f'   panjang teks              : {len(t):,} kar')
print(f'   jumlah baris (\\n)         : {t.count(chr(10)):,}')
print(f'   jumlah baris kosong       : {t.count(chr(10)*2):,}')
print()
print('   --- 400 kar pertama (tanda | = batas baris) ---')
print('   ' + t[:400].replace('\n', ' |\n   '))

print()
print('═' * 74)
print('3. PEMECAH PARAGRAF — apa yang dipakai halaman pembimbing?')
print('═' * 74)
import app.rute_pembimbing as RP                              # noqa: E402
import inspect
src = inspect.getsource(RP._isi_naskah)
print(f'   _isi_naskah: {len(src)} kar kode')
print()
print(src[:1400])
