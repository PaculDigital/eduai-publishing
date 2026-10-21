"""Suntik komentar Word ke dokumen ASLI yang sah (bukan buatan tangan).

Pakai python-docx di venv yang sah, BUKAN rakit XML manual.
"""
import os
import shutil
import zipfile

SUMBER = '/opt/data/services/eduai-publishing/_arsip/contoh-dokumen/skripsi-s1/SKRIPSI-S1-unhas-olahraga-menstruasi.docx'
TUJUAN = '/tmp/skripsi_asli_komentar_pembimbing.docx'

shutil.copy(SUMBER, TUJUAN)

# Sisipkan komentar Word yang sah
COMMENTS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:comment w:id="1" w:author="Dr. Supriyadi, M.M. (Pembimbing 1)" w:date="2026-09-15T09:30:00Z" w:initials="SP">
    <w:p><w:r><w:t>Perbaiki paragraf kedua BAB II, landasan teori belum ada rujukannya.</w:t></w:r></w:p>
  </w:comment>
  <w:comment w:id="2" w:author="Prof. Siti Rahma, Ph.D. (Pembimbing 2)" w:date="2026-09-15T14:10:00Z" w:initials="SR">
    <w:p><w:r><w:t>Ringkas bagian metode, terlalu panjang.</w:t></w:r></w:p>
  </w:comment>
</w:comments>"""

# Baca dokumen, update rels & content_types
with zipfile.ZipFile(TUJUAN, 'r') as zin:
    file_map = {n: zin.read(n) for n in zin.namelist()}

file_map['word/comments.xml'] = COMMENTS_XML.encode('utf-8')

# Update [Content_Types].xml
ct = file_map.get('[Content_Types].xml', b'').decode('utf-8')
if 'wordprocessingml.comments+xml' not in ct:
    ct = ct.replace(
        '</Types>',
        '<Override PartName="/word/comments.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>'
        '</Types>')
    file_map['[Content_Types].xml'] = ct.encode('utf-8')

# Update word/_rels/document.xml.rels
rels = file_map.get('word/_rels/document.xml.rels', b'').decode('utf-8')
if 'comments' not in rels:
    rels = rels.replace(
        '</Relationships>',
        '<Relationship Id="rIdComments99" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" '
        'Target="comments.xml"/></Relationships>')
    file_map['word/_rels/document.xml.rels'] = rels.encode('utf-8')

with zipfile.ZipFile(TUJUAN, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
    for n, data in file_map.items():
        zout.writestr(n, data)

print(f'✅ Berkas sah siap: {TUJUAN} ({os.path.getsize(TUJUAN)} byte)')