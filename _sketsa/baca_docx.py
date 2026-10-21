import re
import zipfile

with zipfile.ZipFile('/app/uploads/3/0fdc31a831c258c9.docx') as z:
    xml = z.read('word/document.xml').decode('utf-8', 'replace')
teks = re.sub(r'<[^>]+>', '', xml)
print('panjang teks:', len(teks.strip()))
print('ISI:', teks.strip()[:200])
