"""CARI AKAR: kenapa kutipan yang diambil DARI paragraf tidak cocok?

Dugaan: kalimat diambil dari TEKS yang sudah dipecah, tapi XML `<w:p>` berisi
    teks dengan pemisah berbeda (run terpisah, tab, dll) → normal() beda.
"""
import pathlib
import re
import sys
import zipfile

sys.path.insert(0, '/app')
from app.tulis_docx import peta_paragraf

DOCX = pathlib.Path('/app/_naskah_bos_uji.docx')
with zipfile.ZipFile(DOCX) as z:
    xml = z.read('word/document.xml').decode('utf-8')

par = peta_paragraf(xml)


def normal(t: str) -> str:
    t = (t or '').lower()
    t = re.sub(r'[\u2018\u2019\u201c\u201d]', '"', t)
    t = re.sub(r'[\u2013\u2014\u2212]', '-', t)
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'[^\w\s\-.,;:()/%"]', '', t)
    return t.strip()


i = 19
teks = par[i]['teks']
print(f'paragraf #{i+1} ({len(teks)} kar):')
print(f'   {teks[:200]!r}')
print()
kalimat = teks.split('. ')[0] + '.'
print(f'kalimat pertama: {kalimat[:150]!r}')
print(f'   normal(kalimat): {normal(kalimat)[:120]!r}')
print(f'   ADA di normal(teks)? {normal(kalimat) in normal(teks)}')
print()

#  Cari paragraf mana pun yang cocok
print('paragraf yang cocok di SELURUH dokumen:')
kena = [j + 1 for j, p in enumerate(par) if normal(kalimat) in normal(p['teks'])]
print(f'   {kena}')

#  Kenapa? Bandingkan karakter demi karakter
print()
print('perbandingan awal kalimat vs paragraf:')
print(f'   kalimat  : {[hex(ord(c)) for c in kalimat[:60]]}')
print(f'   paragraf : {[hex(ord(c)) for c in teks[:60]]}')
print()
print('apakah kalimat == potongan paragraf?', teks.startswith(kalimat))
print('prefix teks   :', repr(teks[:len(kalimat)]))
print('kalimat       :', repr(kalimat))
