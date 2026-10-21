"""V2: suntik komentar Word + JANGKAR di teks (commentRangeStart/End).

Tanpa jangkar, OnlyOffice tidak tahu komentar menempel di teks mana ->
panel komentar tampil kosong. Pelajaran 16Sep26.
"""
import os
import shutil
import zipfile

SUMBER = '/opt/data/services/eduai-publishing/_arsip/contoh-dokumen/skripsi-s1/SKRIPSI-S1-unhas-olahraga-menstruasi.docx'
TUJUAN = '/tmp/skripsi_asli_komentar_v2.docx'

shutil.copy(SUMBER, TUJUAN)

COMMENTS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:comment w:id="1" w:author="Dr. Supriyadi, M.M. (Pembimbing 1)" w:date="2026-09-15T09:30:00Z" w:initials="SP">
    <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Perbaiki paragraf kedua BAB II, landasan teori belum ada rujukannya. Tambahkan minimal 2 jurnal 5 tahun terakhir.</w:t></w:r></w:p>
  </w:comment>
  <w:comment w:id="2" w:author="Prof. Siti Rahma, Ph.D. (Pembimbing 2)" w:date="2026-09-15T14:10:00Z" w:initials="SR">
    <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Ringkas bagian metode, terlalu panjang. Pindahkan detail teknis ke lampiran.</w:t></w:r></w:p>
  </w:comment>
</w:comments>"""

# Jangkar: satu paragraf ber-highlight di AWAL body (sebelum halaman sampul),
# memuat 2 rentang komentar. Paragraf ini jadi "contoh teks yang dikomentari".
JANGKAR_XML = """<w:p>
  <w:pPr><w:spacing w:after="240"/></w:pPr>
  <w:r><w:commentRangeStart w:id="1"/></w:r>
  <w:r><w:rPr><w:highlight w:val="yellow"/></w:rPr><w:t xml:space="preserve">Landasan teori pada BAB II belum mencantumkan rujukan yang jelas.</w:t></w:r>
  <w:r><w:commentRangeEnd w:id="1"/></w:r>
  <w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="1"/></w:r>
  <w:r><w:commentRangeStart w:id="2"/></w:r>
  <w:r><w:rPr><w:highlight w:val="yellow"/></w:rPr><w:t xml:space="preserve"> Metode penelitian terlalu panjang dan berulang.</w:t></w:r>
  <w:r><w:commentRangeEnd w:id="2"/></w:r>
  <w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="2"/></w:r>
</w:p>"""

with zipfile.ZipFile(TUJUAN, 'r') as zin:
    file_map = {n: zin.read(n) for n in zin.namelist()}

# 1. comments.xml
file_map['word/comments.xml'] = COMMENTS_XML.encode('utf-8')

# 2. [Content_Types].xml
ct = file_map.get('[Content_Types].xml', b'').decode('utf-8')
if 'wordprocessingml.comments+xml' not in ct:
    ct = ct.replace('</Types>',
        '<Override PartName="/word/comments.xml" ContentType='
        '"application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/></Types>')
    file_map['[Content_Types].xml'] = ct.encode('utf-8')

# 3. word/_rels/document.xml.rels
rels = file_map.get('word/_rels/document.xml.rels', b'').decode('utf-8')
if 'relationships/comments"' not in rels:
    rels = rels.replace('</Relationships>',
        '<Relationship Id="rIdKomentar1" Type="http://schemas.openxmlformats.org/'
        'officeDocument/2006/relationships/comments" Target="comments.xml"/></Relationships>')
    file_map['word/_rels/document.xml.rels'] = rels.encode('utf-8')

# 4. document.xml — sisipkan jangkar tepat setelah <w:body>
doc = file_map.get('word/document.xml', b'').decode('utf-8')
if 'commentRangeStart' not in doc:
    if '<w:body>' not in doc:
        raise SystemExit('TIDAK ADA <w:body> — struktur tak dikenal')
    doc = doc.replace('<w:body>', '<w:body>' + JANGKAR_XML, 1)
    file_map['word/document.xml'] = doc.encode('utf-8')

with zipfile.ZipFile(TUJUAN, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
    for n, data in file_map.items():
        zout.writestr(n, data)

print(f'✅ Berkas v2 (dengan jangkar): {TUJUAN} ({os.path.getsize(TUJUAN)} byte)')