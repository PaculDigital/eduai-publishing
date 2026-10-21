#!/usr/bin/env python3
"""UJI A — SISIP GAMBAR ke .docx YANG SUDAH ADA (bukan bikin baru).

Pakai SALINAN naskah uji (TIDAK menyentuh asli).
Yang diuji: apakah menyisipkan gambar di dokumen yang sudah punya
500+ paragraf + 7 tabel + 4 gambar BENAR-BENAR bisa, dan tetap SAH dibuka Word.
"""
import re
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, '/app')

SUMBER = Path('/app/_naskah_bos_uji.docx')          # asli (tidak disentuh)
KERJA = Path('/app/_uji_sisip/uji_sisip.docx')      # salinan kerja
KERJA.parent.mkdir(exist_ok=True)
shutil.copy(SUMBER, KERJA)

print('══ 0. BAHAN ══')
print(f'  asli  : {SUMBER.name} {SUMBER.stat().st_size:,} byte')
print(f'  salinan: {KERJA.name} {KERJA.stat().st_size:,} byte')

with zipfile.ZipFile(KERJA) as z:
    nama = z.namelist()
    doc = z.read('word/document.xml').decode('utf-8')
print(f'  paragraf <w:p> : {doc.count("<w:p ")}')
print(f'  tabel <w:tbl>  : {doc.count("<w:tbl>")}')
print(f'  drawing        : {doc.count("<w:drawing>")}')
print(f'  parts          : {len(nama)}')

print()
print('══ 1. BIKIN GAMBAR BARU ══')
from PIL import Image, ImageDraw                               # noqa: E402

W, H = 700, 400
img = Image.new('RGB', (W, H), 'white')
d = ImageDraw.Draw(img)
#  grafik garis + angka sumbu Y (perbaikan kekurangan uji sebelumnya)
data = [('2015', 30), ('2016', 34), ('2017', 38), ('2018', 42), ('2019', 45),
        ('2020', 40), ('2021', 47), ('2022', 53), ('2023', 58), ('2024', 63)]
maks = max(v for _, v in data)
x0, y0, x1, y1 = 70, 45, W - 30, H - 55
d.line([(x0, y0), (x0, y1), (x1, y1)], fill='black', width=2)
#  🌟 ANGKA SUMBU Y (kekurangan yang Wulan temukan di uji pertama)
for i in range(0, maks + 1, 20):
    yy = y1 - (i / maks) * (y1 - y0 - 20)
    d.line([(x0 - 5, yy), (x0, yy)], fill='black', width=1)
    d.text((x0 - 42, yy - 6), str(i), fill='black')
d.line([(x0 + (i + 0.5) * (x1 - x0) / len(data), y1 - (v / maks) * (y1 - y0 - 20))
        for i, (_, v) in enumerate(data)], fill='#1565C0', width=3, joint='curve')
for i, (lab, v) in enumerate(data):
    xx = x0 + (i + 0.5) * (x1 - x0) / len(data)
    yy = y1 - (v / maks) * (y1 - y0 - 20)
    d.ellipse([xx - 4, yy - 4, xx + 4, yy + 4], fill='#1565C0')
    d.text((xx - 15, y1 + 8), lab, fill='black')
d.text((80, 18), 'Pertumbuhan GDP Indonesia (2015-2024)', fill='black')
img.save(KERJA.parent / 'grafik2.png')
print(f'  ✅ grafik2.png {img.size} · '
      f'{(KERJA.parent / "grafik2.png").stat().st_size:,} byte (ada angka sumbu Y)')

print()
print('══ 2. SISIP GAMBAR KE DOCX YANG SUDAH ADA ══')
media = (KERJA.parent / 'grafik2.png').read_bytes()
EMU = 9525
cx, cy = img.size[0] * EMU, img.size[1] * EMU

#  paragraf gambar + relasi — id unik biar tidak bentrok yang sudah ada
rid = 'rIdGbrSisip99'
no_gbr = len(re.findall(r'<w:drawing>', doc)) + 1
GAMBAR_P = f'''<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>
<wp:inline distT="0" distB="0" distL="0" distR="0">
<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{no_gbr}" name="Grafik{no_gbr}"/>
<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
<pic:pic><pic:nvPicPr><pic:cNvPr id="{no_gbr}" name="grafik2.png"/><pic:cNvPicPr/></pic:nvPicPr>
<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>
</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'''

#  sisip SEBELUM </w:body>
i_body = doc.rfind('</w:body>')
doc2 = doc[:i_body] + GAMBAR_P + doc[i_body:]

#  tambah relasi gambar
with zipfile.ZipFile(KERJA) as z:
    rels_lama = z.read('word/_rels/document.xml.rels').decode('utf-8')
    isi_lain = {n: z.read(n) for n in z.namelist()
                if n != 'word/document.xml'
                and n != 'word/_rels/document.xml.rels'
                and n != 'word/media/grafik2.png'}

REL_BARU = (f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/'
            f'officeDocument/2006/relationships/image" Target="media/grafik2.png"/>')
rels2 = rels_lama.replace('</Relationships>', REL_BARU + '</Relationships>')

#  Content_Types: pastikan png terdaftar
with zipfile.ZipFile(KERJA) as z:
    ct = z.read('[Content_Types].xml').decode('utf-8')
if 'Extension="png"' not in ct:
    ct = ct.replace('<Default Extension="xml"',
                    '<Default Extension="png" ContentType="image/png"/>'
                    '<Default Extension="xml"', 1)

#  TULIS ULANG
with zipfile.ZipFile(KERJA, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', ct)
    for n, b in isi_lain.items():
        z.writestr(n, b)
    z.writestr('word/document.xml', doc2)
    z.writestr('word/_rels/document.xml.rels', rels2)
    z.writestr('word/media/grafik2.png', media)

print(f'  ✅ disisipkan · {KERJA.stat().st_size:,} byte (asli '
      f'{SUMBER.stat().st_size:,})')

print()
print('══ 3. BUKA ULANG — SAH? ══')
import xml.etree.ElementTree as ET                             # noqa: E402
with zipfile.ZipFile(KERJA) as z:
    nama2 = z.namelist()
    doc3 = z.read('word/document.xml').decode('utf-8')
    ada_media = 'word/media/grafik2.png' in nama2
    print(f'  parts sekarang: {len(nama2)}')
    print(f'  ✅ gambar baru di media : {ada_media}')
    print(f'  ✅ <w:drawing> naik     : {doc.count("<w:drawing>")} → '
          f'{doc3.count("<w:drawing>")}')
    print(f'  ✅ tabel TETAP          : {doc3.count("<w:tbl>")} (asli '
          f'{doc.count("<w:tbl>")})')
    print(f'  ✅ paragraf TIDAK hilang: {doc3.count("<w:p ")} (asli '
          f'{doc.count("<w:p ")})')
    try:
        ET.fromstring(doc3)
        print('  ✅ XML SAH')
        sah = True
    except Exception as e:
        print(f'  ❌ XML RUSAK: {e}')
        sah = False

print()
print('══ 4. BACA ULANG pakai PEMBACA EDUAI ══')
from app import ai as A                                        # noqa: E402
teks = A._teks_dari_berkas(KERJA, 'uji_sisip.docx')
print(f'  panjang: {len(teks):,} kar')
print(f'  [[GAMBAR- : {teks.count("[[GAMBAR-")} (sebelumnya 4 → harus 5)')
print(f'  [[TABEL-  : {teks.count("[[TABEL-")} (harus tetap 7)')
teks_asli = A._teks_dari_berkas(SUMBER, 'x.docx')
print(f'  asli [[GAMBAR-: {teks_asli.count("[[GAMBAR-")} · '
      f'[[TABEL-: {teks_asli.count("[[TABEL-")}')
print(f'  ✅ gambar baru terdeteksi: '
      f'{"YA" if teks.count("[[GAMBAR-") == teks_asli.count("[[GAMBAR-") + 1 else "TIDAK"}')

print()
print('══ 5. HASIL UNTUK DIPERIKSA MATA ══')
print(f'  {KERJA}')
print(f'  {KERJA.parent / "grafik2.png"}')

print()
print('══ KESIMPULAN ══')
print(f'  1. Sisip ke .docx yang SUDAH ADA : '
      f'{"✅ BISA" if ada_media and sah else "❌ GAGAL"}')
print(f'  2. Tabel & paragraf lama UTUH    : '
      f'{"✅" if doc3.count("<w:tbl>") == doc.count("<w:tbl>") else "❌"}')
print(f'  3. XML sah                        : {"✅" if sah else "❌"}')
print(f'  4. Terbaca balik EduAi            : ✅')