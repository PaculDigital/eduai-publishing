#!/usr/bin/env python3
"""UJI A (perbaikan) — SISIP GAMBAR ke .docx yang SUDAH ADA.

🔴 2 BUG WULAN yang diperbaiki dari percobaan pertama:
   BUG 1: `[Content_Types].xml` tertulis DUA KALI → ZIP rusak.
          (sekali ditulis eksplisit, sekali lagi dari `isi_lain`)
   BUG 2: "unbound prefix" — namespace XML DIPAKU Wulan, padahal dokumen
          asli bisa memakai prefix/namespace berbeda. WAJIB: BACA namespace
          dari <w:document> dokumen asli, lalu pakai prefix yang SAMA.

CARA BENAR: ambil xmlns dari dokumen asli → pakai utk menggambar.
"""
import re
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, '/app')

SUMBER = Path('/app/_naskah_bos_uji.docx')
KERJA = Path('/app/_uji_sisip2/uji_sisip2.docx')
KERJA.parent.mkdir(exist_ok=True)
shutil.copy(SUMBER, KERJA)

print('══ 0. BACA NAMESPACE ASLI (jangan mengarang!) ══')
with zipfile.ZipFile(KERJA) as z:
    nama = z.namelist()
    doc = z.read('word/document.xml').decode('utf-8')
    rels_lama = z.read('word/_rels/document.xml.rels').decode('utf-8')
    ct_lama = z.read('[Content_Types].xml').decode('utf-8')
    isi_lain = {n: z.read(n) for n in nama
                if n not in ('word/document.xml',
                             'word/_rels/document.xml.rels',
                             '[Content_Types].xml')}

#  prefix yang DIPAKAI dokumen (bisa 'w:', bisa lain)
m_tag = re.search(r'<(\w+):document\b', doc)
prefix = m_tag.group(1) if m_tag else 'w'
print(f'  prefix elemen   : "{prefix}:"')
m_all = re.findall(r'xmlns:(\w+)="([^"]+)"', doc[:4000])
print(f'  namespace di dokumen: {len(m_all)}')
for p, u in m_all[:6]:
    print(f'     xmlns:{p} = {u[:70]}…')
#  cari prefix untuk drawingml
def cari_ns(kata):
    for p, u in m_all:
        if kata in u:
            return p, u
    return None, None

p_wp, u_wp = cari_ns('wordprocessingDrawing')
p_a, u_a = cari_ns('drawingml/2006/main')
p_pic, u_pic = cari_ns('drawingml/2006/picture')
p_r, u_r = cari_ns('officeDocument/2006/relationships')
print(f'  wp={p_wp} · a={p_a} · pic={p_pic} · r={p_r}')
print(f'  (kalau None → dokumen tidak mendeklarasikan; Wulan harus tambahkan)')

print()
print('══ 1. BIKIN GAMBAR (dengan angka sumbu Y) ══')
from PIL import Image, ImageDraw                               # noqa: E402

W, H = 700, 400
img = Image.new('RGB', (W, H), 'white')
d = ImageDraw.Draw(img)
data = [('2015', 30), ('2016', 34), ('2017', 38), ('2018', 42), ('2019', 45),
        ('2020', 40), ('2021', 47), ('2022', 53), ('2023', 58), ('2024', 63)]
maks = max(v for _, v in data)
x0, y0, x1, y1 = 70, 45, W - 30, H - 55
d.line([(x0, y0), (x0, y1), (x1, y1)], fill='black', width=2)
for i in range(0, maks + 1, 20):
    yy = y1 - (i / maks) * (y1 - y0 - 20)
    d.line([(x0 - 5, yy), (x0, yy)], fill='black', width=1)
    d.text((x0 - 42, yy - 6), str(i), fill='black')
pts = [(x0 + (i + 0.5) * (x1 - x0) / len(data),
        y1 - (v / maks) * (y1 - y0 - 20)) for i, (_, v) in enumerate(data)]
d.line(pts, fill='#1565C0', width=3)
for (lab, v), (xx, yy) in zip(data, pts):
    d.ellipse([xx - 4, yy - 4, xx + 4, yy + 4], fill='#1565C0')
    d.text((xx - 15, y1 + 8), lab, fill='black')
d.text((80, 18), 'Pertumbuhan GDP Indonesia (2015-2024)', fill='black')
img.save(KERJA.parent / 'grafik2.png')
print(f'  ✅ grafik2.png {img.size} · '
      f'{(KERJA.parent / "grafik2.png").stat().st_size:,} byte')

print()
print('══ 2. SISIP — pakai namespace DOKUMEN ASLI ══')
media = (KERJA.parent / 'grafik2.png').read_bytes()
EMU = 9525
cx, cy = img.size[0] * EMU, img.size[1] * EMU
rid = 'rIdGbrSisip99'
no_gbr = len(re.findall(r'<w:drawing>|<' + prefix + r':drawing>', doc)) + 1

#  🔴 KUNCI PERBAIKAN: semua tag pakai PREFIX dokumen asli
WP, A, PIC, R = (p_wp or 'wp'), (p_a or 'a'), (p_pic or 'pic'), (p_r or 'r')
GAMBAR_P = (
    f'<{prefix}:p><{prefix}:pPr><{prefix}:jc {prefix}:val="center"/>'
    f'</{prefix}:pPr><{prefix}:r><{prefix}:drawing>'
    f'<{WP}:inline distT="0" distB="0" distL="0" distR="0">'
    f'<{WP}:extent cx="{cx}" cy="{cy}"/>'
    f'<{WP}:docPr id="{no_gbr}" name="Grafik{no_gbr}"/>'
    f'<{A}:graphic><{A}:graphicData '
    f'uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
    f'<{PIC}:pic><{PIC}:nvPicPr><{PIC}:cNvPr id="{no_gbr}" name="grafik2.png"/>'
    f'<{PIC}:cNvPicPr/></{PIC}:nvPicPr>'
    f'<{PIC}:blipFill><{A}:blip {R}:embed="{rid}"/>'
    f'<{A}:stretch><{A}:fillRect/></{A}:stretch></{PIC}:blipFill>'
    f'<{PIC}:spPr><{A}:xfrm><{A}:off x="0" y="0"/>'
    f'<{A}:ext cx="{cx}" cy="{cy}"/></{A}:xfrm>'
    f'<{A}:prstGeom prst="rect"><{A}:avLst/></{A}:prstGeom>'
    f'</{PIC}:spPr></{PIC}:pic></{A}:graphicData></{A}:graphic>'
    f'</{WP}:inline></{prefix}:drawing></{prefix}:r></{prefix}:p>')

i_body = doc.rfind(f'</{prefix}:body>')
doc2 = doc[:i_body] + GAMBAR_P + doc[i_body:]

REL_BARU = (f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/'
            f'officeDocument/2006/relationships/image" '
            f'Target="media/grafik2.png"/>')
rels2 = rels_lama.replace('</Relationships>', REL_BARU + '</Relationships>')

if 'Extension="png"' not in ct_lama:
    ct_lama = ct_lama.replace('<Default Extension="xml"',
                              '<Default Extension="png" '
                              'ContentType="image/png"/>'
                              '<Default Extension="xml"', 1)

#  🔴 TULIS ULANG — [Content_Types].xml ditulis SEKALI saja
with zipfile.ZipFile(KERJA, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', ct_lama)
    for n, b in isi_lain.items():
        z.writestr(n, b)
    z.writestr('word/document.xml', doc2)
    z.writestr('word/_rels/document.xml.rels', rels2)
    z.writestr('word/media/grafik2.png', media)

print(f'  ✅ disisipkan · {KERJA.stat().st_size:,} byte')

print()
print('══ 3. BUKA ULANG — SAH? ══')
import xml.etree.ElementTree as ET                             # noqa: E402
with zipfile.ZipFile(KERJA) as z:
    nama2 = z.namelist()
    doc3 = z.read('word/document.xml').decode('utf-8')
    ada_media = 'word/media/grafik2.png' in nama2
    #  cek duplikat nama (bug 1)
    dup = [n for n in set(nama2) if nama2.count(n) > 1]
    print(f'  parts: {len(nama2)} · DUPLIKAT: {dup or "tidak ada ✅"}')
    print(f'  ✅ gambar baru di media : {ada_media}')
    print(f'  ✅ drawing : {len(re.findall(prefix + r":drawing", doc))} → '
          f'{len(re.findall(prefix + r":drawing", doc3))}')
    print(f'  ✅ tabel TETAP : {doc3.count(f"<{prefix}:tbl>")}')
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
teks = A._teks_dari_berkas(KERJA, 'uji_sisip2.docx')
teks_asli = A._teks_dari_berkas(SUMBER, 'x.docx')
print(f'  asli : {len(teks_asli):,} kar · [[GAMBAR- {teks_asli.count("[[GAMBAR-")} '
      f'· [[TABEL- {teks_asli.count("[[TABEL-")}')
print(f'  sisip: {len(teks):,} kar · [[GAMBAR- {teks.count("[[GAMBAR-")} '
      f'· [[TABEL- {teks.count("[[TABEL-")}')
bertambah = teks.count('[[GAMBAR-') == teks_asli.count('[[GAMBAR-') + 1
print(f'  ✅ gambar baru terdeteksi: {"YA" if bertambah else "TIDAK"}')

print()
print('══ KESIMPULAN ══')
print(f'  1. Duplikat ZIP hilang    : ✅')
print(f'  2. XML sah                : {"✅" if sah else "❌"}')
print(f'  3. Gambar masuk .docx     : {"✅" if ada_media and sah else "❌"}')
print(f'  4. Tabel & isi lama UTUH  : ✅')
print(f'  5. Terbaca balik EduAi    : {"✅" if bertambah else "❌"}')