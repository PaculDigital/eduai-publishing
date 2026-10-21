"""Buat dokumen .docx dengan komentar Word asli di margin + komentar pembimbing nyata.

Pakai python-docx di venv: /opt/data/.venv/bin/python3
"""
import zipfile
from pathlib import Path

OUT = Path('/tmp/skripsi_dengan_komentar_pembimbing.docx')

# 1. Dokumen XML dasar
DOCUMENT_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading1"/><w:jc w:val="center"/></w:pPr>
      <w:r><w:rPr><w:b/><w:sz w:val="28"/></w:rPr><w:t>BAB I PENDAHULUAN</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading2"/></w:pPr>
      <w:r><w:rPr><w:b/><w:sz w:val="24"/></w:rPr><w:t>1.1 Latar Belakang Masalah</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t xml:space="preserve">Perkembangan teknologi informasi pada era digital membawa perubahan signifikan terhadap pola kerja organisasi. </w:t></w:r>
      <w:commentRangeStart w:id="1"/>
      <w:r>
        <w:rPr><w:highlight w:val="yellow"/></w:rPr>
        <w:t>Banyak perusahaan yang belum siap menghadapi perubahan ini sehingga produktivitas menurun drastis.</w:t>
      </w:r>
      <w:commentRangeEnd w:id="1"/>
      <w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="1"/></w:r>
      <w:r><w:t xml:space="preserve"> Fenomena ini menuntut adanya kepemimpinan yang adaptif dan mampu menginspirasi bawahan.</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t xml:space="preserve">Kepemimpinan transformasional diyakini mampu mendorong inovasi dan komitmen karyawan. Namun demikian, </w:t></w:r>
      <w:commentRangeStart w:id="2"/>
      <w:r>
        <w:rPr><w:highlight w:val="yellow"/></w:rPr>
        <w:t>beberapa penelitian terdahulu menunjukkan hasil yang tidak konsisten mengenai hubungan langsung antara kepemimpinan transformasional dan kinerja.</w:t>
      </w:r>
      <w:commentRangeEnd w:id="2"/>
      <w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="2"/></w:r>
      <w:r><w:t xml:space="preserve"> Oleh karena itu, diperlukan variabel mediasi seperti motivasi kerja untuk memperjelas mekanisme pengaruh tersebut.</w:t></w:r>
    </w:p>
    <w:p>
      <w:commentRangeStart w:id="3"/>
      <w:r>
        <w:rPr><w:highlight w:val="yellow"/></w:rPr>
        <w:t>Penelitian ini dilakukan pada PT Maju Bersama dengan sampel 100 karyawan.</w:t>
      </w:r>
      <w:commentRangeEnd w:id="3"/>
      <w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="3"/></w:r>
    </w:p>
    <w:sectPr/>
  </w:body>
</w:document>"""

# 2. XML Komentar asli Word (ditampilkan di margin kanan oleh OnlyOffice/Word)
COMMENTS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:comment w:id="1" w:author="Dr. Supriyadi, M.M. (Pembimbing 1)" w:date="2026-09-15T09:30:00Z" w:initials="SP">
    <w:p>
      <w:r><w:rPr><w:b/><w:color w:val="B3261E"/></w:rPr><w:t>[Komentar 1 — Data &amp; Rujukan]</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>Klaim "produktivitas menurun drastis" ini terlalu berani kalau tanpa data pendukung. Tolong masukkan data statistik riil (survei BPS / laporan industri 2024-2025) atau kutip rujukan yang relevan. Jangan asal sebut.</w:t></w:r>
    </w:p>
  </w:comment>

  <w:comment w:id="2" w:author="Dr. Supriyadi, M.M. (Pembimbing 1)" w:date="2026-09-15T09:35:00Z" w:initials="SP">
    <w:p>
      <w:r><w:rPr><w:b/><w:color w:val="B3261E"/></w:rPr><w:t>[Komentar 2 — Research Gap]</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>Bagus, research gap sudah mulai kelihatan. Tapi sebutkan secara spesifik: penelitian siapa yang hasilnya positif dan siapa yang tidak signifikan? Minimal 2 jurnal bereputasi 5 tahun terakhir (2021-2026).</w:t></w:r>
    </w:p>
  </w:comment>

  <w:comment w:id="3" w:author="Prof. Siti Rahma, Ph.D. (Pembimbing 2)" w:date="2026-09-15T14:10:00Z" w:initials="SR">
    <w:p>
      <w:r><w:rPr><w:b/><w:color w:val="1E56B3"/></w:rPr><w:t>[Komentar 3 — Konteks Lokasi]</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>Mengapa memilih PT Maju Bersama sebagai objek penelitian? Apa urgensi dan masalah spesifik di perusahaan ini dibanding tempat lain? Tambahkan 1-2 paragraf tentang fenomena bisnis di lokasi tersebut.</w:t></w:r>
    </w:p>
  </w:comment>
</w:comments>"""

RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
</Relationships>"""

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
</Types>"""

PACKAGE_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

# Tulis zip docx
with zipfile.ZipFile(OUT, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', CONTENT_TYPES)
    z.writestr('_rels/.rels', PACKAGE_RELS)
    z.writestr('word/document.xml', DOCUMENT_XML)
    z.writestr('word/comments.xml', COMMENTS_XML)
    z.writestr('word/_rels/document.xml.rels', RELS_XML)

print(f'✅ Berkas dibuat: {OUT} ({OUT.stat().st_size} byte)')