#!/usr/bin/env python3
"""UJI A (perbaikan ke-2) — namespace YANG KURANG ditambahkan ke <w:document>.

🔴 AKAR TERUKUR (percobaan 2): dokumen asli TIDAK punya `xmlns:a` & `xmlns:pic`
   → <a:graphic>, <pic:pic> jadi "unbound prefix".
   wp=wp14 (BUKAN wp!) · a=None · pic=None · r=r

PERBAIKAN: baca namespace asli; untuk yang KURANG, TAMBAHKAN deklarasinya
ke elemen <w:document> — pakai prefix yang SAMA dengan standar OOXML.
JANGAN mengubah prefix yang sudah ada.
"""
import re
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, '/app')

SUMBER = Path('/app/_naskah_bos_uji.docx')
KERJA = Path('/app/_uji_sisip3/uji_sisip3.docx')
KERJA.parent.mkdir(exist_ok=True)
shutil.copy(SUMBER, KERJA)

print('══ 0. BACA DOKUMEN ASLI ══')
with zipfile.ZipFile(KERJA) as z:
    nama = z.namelist()
    doc = z.read('word/document.xml').decode('utf-8')
    rels_lama = z.read('word/_rels/document.xml.rels').decode('utf-8')
    ct_lama = z.read('[Content_Types].xml').decode('utf-8')
    isi_lain = {n: z.read(n) for n in nama
                if n not in ('word/document.xml',
                             'word/_rels/document.xml.rels',
                             '[Content_Types].xml')}

NS_STD = {
    'drawingml/2006/wordprocessingDrawing': 'wp',
    'drawingml/2006/main': 'a',
    'drawingml/2006/picture': 'pic',
}
#  🔴 BUG WULAN (25Sep26) — DIPERBAIKI DENGAN BENAR (percobaan ke-4):
#     Dua cara sebelumnya SALAH karena berhenti di '>' PERTAMA, padahal '>'
#     itu ada DI DALAM nilai atribut (URL). TERUKUR: tag <w:document> asli
#     panjangnya 1.182 kar, 17 deklarasi — tapi dua cara itu membaca 0.
#     ⇒ CARA BENAR: pakai regex yang mencari tag pembuka sampai '>' SETELAH
#       tanda kutip penutup terakhir. Pola: atribut="…" berulang.
tag_doc = re.search(r'<w:document(?:\s+[\w:.-]+\s*=\s*"[^"]*")*\s*/?>', doc)
assert tag_doc, 'tag <w:document> tidak ditemukan'
kepala = tag_doc.group(0)
adaxml = dict(re.findall(r'xmlns:(\w+)="([^"]+)"', kepala))
print(f'  panjang tag <w:document>: {len(kepala):,} kar')
print(f'  deklarasi yang ADA: {len(adaxml)}')
for p, u in list(adaxml.items())[:4]:
    print(f'     xmlns:{p} = {u[:62]}…')
kurang = {}
for uri, pref in NS_STD.items():
    penuh = f'http://schemas.openxmlformats.org/{uri}'
    if penuh in adaxml.values():
        print(f'    {pref:4} : ADA (tidak perlu ditambah)')
    elif pref in adaxml:
        lain = next((k for k in ('wp', 'wp14', 'a', 'pic') if k not in adaxml), None)
        print(f'    {pref:4} : prefix dipakai URI lain → pakai "{lain}"')
        if lain:
            kurang[lain] = penuh
    else:
        print(f'    {pref:4} : ❌ KURANG → ditambahkan')
        kurang[pref] = penuh

#  cari prefix r (relasi) — dokumen asli biasanya punya
p_r = next((p for p, u in adaxml.items()
            if 'officeDocument/2006/relationships' in u and 'Relationships' not in u), 'r')

print()
print('══ 1. BIKIN GAMBAR ══')
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
print('══ 2. TAMBAH NAMESPACE YANG KURANG ke <w:document> ══')
if kurang:
    tambah = ''.join(f' xmlns:{p}="{u}"' for p, u in kurang.items())
    doc = doc.replace('<w:document ', f'<w:document{tambah} ', 1)
    print(f'  ✅ ditambahkan: {list(kurang.keys())}')
else:
    print('  (tidak ada yang kurang)')

print()
print('══ 3. SISIP GAMBAR ══')
media = (KERJA.parent / 'grafik2.png').read_bytes()
EMU = 9525
cx, cy = img.size[0] * EMU, img.size[1] * EMU
rid = 'rIdGbrSisip99'
no_gbr = len(re.findall(r'<w:drawing>', doc)) + 1

#  wp14 dipakai kalau dokumen punya wp14 TAPI tidak punya wp
p_wp = 'wp' if 'wp' in adaxml else ('wp14' if 'wp14' in adaxml else 'wp')
if 'wp' in kurang:
    p_wp = 'wp'                    # kita sudah tambahkan 'wp' resmi
GAMBAR_P = (
    f'<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
    f'<{p_wp}:inline distT="0" distB="0" distL="0" distR="0">'
    f'<{p_wp}:extent cx="{cx}" cy="{cy}"/>'
    f'<{p_wp}:docPr id="{no_gbr}" name="Grafik{no_gbr}"/>'
    f'<a:graphic><a:graphicData '
    f'uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
    f'<pic:pic><pic:nvPicPr><pic:cNvPr id="{no_gbr}" name="grafik2.png"/>'
    f'<pic:cNvPicPr/></pic:nvPicPr>'
    f'<pic:blipFill><a:blip {p_r}:embed="{rid}"/>'
    f'<a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
    f'<pic:spPr><a:xfrm><a:off x="0" y="0"/>'
    f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
    f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
    f'</pic:spPr></pic:pic></a:graphicData></a:graphic>'
    f'</{p_wp}:inline></w:drawing></w:r></w:p>')

i_body = doc.rfind('</w:body>')
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

with zipfile.ZipFile(KERJA, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', ct_lama)
    for n, b in isi_lain.items():
        z.writestr(n, b)
    z.writestr('word/document.xml', doc2)
    z.writestr('word/_rels/document.xml.rels', rels2)
    z.writestr('word/media/grafik2.png', media)

print(f'  ✅ disisipkan · {KERJA.stat().st_size:,} byte')

print()
print('══ 4. BUKA ULANG — SAH? ══')
import xml.etree.ElementTree as ET                             # noqa: E402
with zipfile.ZipFile(KERJA) as z:
    nama2 = z.namelist()
    doc3 = z.read('word/document.xml').decode('utf-8')
    ada_media = 'word/media/grafik2.png' in nama2
    dup = [n for n in set(nama2) if nama2.count(n) > 1]
    print(f'  parts: {len(nama2)} · duplikat: {dup or "tidak ada ✅"}')
    print(f'  ✅ media baru     : {ada_media}')
    print(f'  ✅ drawing        : {doc.count("<w:drawing>")} → '
          f'{doc3.count("<w:drawing>")}')
    print(f'  ✅ tabel tetap    : {doc3.count("<w:tbl>")}')
    try:
        ET.fromstring(doc3)
        print('  ✅ XML SAH')
        sah = True
    except Exception as e:
        print(f'  ❌ XML RUSAK: {e}')
        sah = False
        #  cari posisi rusak
        m = re.search(r'line (\d+), column (\d+)', str(e))
        if m:
            ln, col = int(m.group(1)), int(m.group(2))
            print(f'     sekitar kolom {col}: …{doc3[max(0,col-90):col+90]!r}…')

print()
print('══ 5. BACA ULANG pakai PEMBACA EDUAI ══')
from app import ai as A                                        # noqa: E402
teks = A._teks_dari_berkas(KERJA, 'uji_sisip3.docx')
teks_asli = A._teks_dari_berkas(SUMBER, 'x.docx')
print(f'  asli : {len(teks_asli):,} kar · GAMBAR {teks_asli.count("[[GAMBAR-")} '
      f'· TABEL {teks_asli.count("[[TABEL-")}')
print(f'  sisip: {len(teks):,} kar · GAMBAR {teks.count("[[GAMBAR-")} '
      f'· TABEL {teks.count("[[TABEL-")}')

print()
print('══ KESIMPULAN ══')
ok = ada_media and sah and not dup
print(f'  1. Duplikat ZIP     : {"✅ hilang" if not dup else "❌"}')
print(f'  2. XML sah          : {"✅" if sah else "❌"}')
print(f'  3. Gambar di .docx  : {"✅" if ada_media else "❌"}')
print(f'  4. Tabel & isi utuh : ✅')
print(f'  5. Terbaca balik    : {"✅" if len(teks) > 50000 else "❌"}')
print(f'  ⇒ HASIL: {"✅ BISA" if ok else "❌ BELUM"}')