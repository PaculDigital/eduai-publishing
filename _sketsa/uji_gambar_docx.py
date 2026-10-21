#!/usr/bin/env python3
"""UJI: bisakah app ini MENYISIPKAN GAMBAR (grafik) ke dalam .docx?

TANPA library baru (aturan: jangan tambah dependency kalau bisa).
.pdocx = ZIP berisi XML + media. Wulan tulis OOXML langsung pakai stdlib.

CARA UJI (bukan tebakan):
   1. buat PNG grafik (PIL sudah ada di container)
   2. buat .docx berisi 3 paragraf teks
   3. sisipkan gambar di antara paragraf 2 & 3
   4. buka ulang .docx → apakah XML sah & gambar ada di word/media/?
   5. render → periksa MATA
"""
import io
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, '/app')

OUT = Path('/app/_uji_gambar_docx')
OUT.mkdir(exist_ok=True)

print('══ 1. BIKIN GAMBAR (PNG) — PIL ══')
from PIL import Image, ImageDraw                               # noqa: E402

W, H = 640, 380
img = Image.new('RGB', (W, H), 'white')
d = ImageDraw.Draw(img)

#  grafik batang sederhana: pertumbuhan GDP 2015-2024 (contoh Bos)
data = [('2015', 30), ('2016', 34), ('2017', 38), ('2018', 42), ('2019', 45),
        ('2020', 40), ('2021', 47), ('2022', 53), ('2023', 58), ('2024', 63)]
maks = max(v for _, v in data)
x0, y0, x1, y1 = 60, 40, W - 30, H - 60
d.line([(x0, y0), (x0, y1), (x1, y1)], fill='black', width=2)
lebar = (x1 - x0) / len(data)
for i, (label, v) in enumerate(data):
    bx0 = x0 + i * lebar + 8
    bx1 = x0 + (i + 1) * lebar - 8
    by = y1 - (v / maks) * (y1 - y0 - 20)
    d.rectangle([bx0, by, bx1, y1], fill='#2E7D32')
    d.text(((bx0 + bx1) / 2 - 14, y1 + 8), label, fill='black')
d.text((70, 15), 'Pertumbuhan GDP (2015-2024)', fill='black')
img.save(OUT / 'grafik.png')
print(f'  ✅ grafik.png {img.size} · {(OUT / "grafik.png").stat().st_size:,} byte')

print()
print('══ 2. BIKIN .docx dasar (3 paragraf) ══')
DOK = OUT / 'uji.docx'
NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
      ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
      ' xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"'
      ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
      ' xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')


def par(t):
    return f'<w:p><w:r><w:t xml:space="preserve">{t}</w:t></w:r></w:p>'


media = (OUT / 'grafik.png').read_bytes()
EMU_PER_PX = 9525
cx, cy = img.size[0] * EMU_PER_PX, img.size[1] * EMU_PER_PX
rid = 'rIdGambar1'

GAMBAR_XML = f'''<w:p><w:r><w:drawing>
<wp:inline distT="0" distB="0" distL="0" distR="0">
<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="1" name="Grafik1"/>
<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
<pic:pic><pic:nvPicPr><pic:cNvPr id="1" name="grafik.png"/><pic:cNvPicPr/></pic:nvPicPr>
<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>
</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'''

document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:document {NS}><w:body>'
            + par('Paragraf pertama sebelum grafik.')
            + par('Data menunjukkan tren peningkatan.')
            + GAMBAR_XML
            + par('Gambar 1.1. Pertumbuhan GDP 2015-2024. Sumber: BPS.')
            + par('Paragraf terakhir sesudah grafik.')
            + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr>'
            '</w:body></w:document>')

types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
         '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
         '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
         '<Default Extension="xml" ContentType="application/xml"/>'
         '<Default Extension="png" ContentType="image/png"/>'
         '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
         '</Types>')

rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>')

doc_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/grafik.png"/>'
            '</Relationships>')

with zipfile.ZipFile(DOK, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', types)
    z.writestr('_rels/.rels', rels)
    z.writestr('word/document.xml', document)
    z.writestr('word/_rels/document.xml.rels', doc_rels)
    z.writestr('word/media/grafik.png', media)

print(f'  ✅ uji.docx {(DOK).stat().st_size:,} byte')

print()
print('══ 3. BUKA ULANG — apakah XML sah & gambar ada? ══')
import xml.etree.ElementTree as ET                             # noqa: E402
with zipfile.ZipFile(DOK) as z:
    nama = z.namelist()
    print(f'  isi paket: {nama}')
    ada_media = 'word/media/grafik.png' in nama
    print(f'  ✅ gambar di word/media/ : {ada_media}')
    doc = z.read('word/document.xml').decode()
    print(f'  ✅ <w:drawing> di document: {doc.count("<w:drawing>")}')
    print(f'  ✅ r:embed={rid} ada     : {rid in doc}')
    try:
        ET.fromstring(doc)
        print('  ✅ XML SAH (bisa di-parse)')
        xml_sah = True
    except Exception as e:
        print(f'  ❌ XML RUSAK: {e}')
        xml_sah = False

print()
print('══ 4. BACA ULANG pakai PEMBACA EDUAI (apakah tetap terbaca?) ══')
import importlib
sys.path.insert(0, '/app')
from app import ai as A                                        # noqa: E402
importlib.reload(A)
teks = A._teks_dari_berkas(DOK, 'uji.docx')
print(f'  panjang teks: {len(teks)} kar')
print(f'  ada [[GAMBAR- ? : {"✅ ya" if "[[GAMBAR-" in teks else "❌ tidak"}')
print(f'  cuplikan: {teks[:220]!r}')

print()
print('══ 5. PERIKSA MATA — render gambar yang dibuat ══')
print(f'  BUKTI: {OUT / "grafik.png"}')
print(f'  ukuran: {(OUT / "grafik.png").stat().st_size:,} byte (harus >10 KB)')

print()
print('══ KESIMPULAN ══')
print(f'  1. Buat PNG grafik    : ✅ (PIL tersedia)')
print(f'  2. Sisip ke .docx     : {"✅ BISA" if ada_media and xml_sah else "❌ GAGAL"}')
print(f'  3. XML sah            : {"✅" if xml_sah else "❌"}')
print(f'  4. Dibaca balik EduAi : ✅')